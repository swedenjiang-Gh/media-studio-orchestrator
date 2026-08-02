"""Build a local InsightFace reference library from Lightroom person labels."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def read_face_rows(path):
    """Return Lightroom face rows that name a person and point to a source image."""
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return [row for row in csv.DictReader(handle) if row.get("person") and row.get("photo_path")]


def read_image(path):
    """Decode a local image through bytes so Windows Unicode paths remain supported."""
    import cv2

    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except FileNotFoundError:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def labeled_box(row, width, height):
    """Convert a Lightroom normalized face quadrilateral into an axis-aligned pixel box."""
    xs = [float(row[key]) * width for key in ("tl_x", "tr_x", "br_x", "bl_x")]
    ys = [float(row[key]) * height for key in ("tl_y", "tr_y", "br_y", "bl_y")]
    return min(xs), min(ys), max(xs), max(ys)


def select_labeled_face(row, width, height, detections, minimum_coverage=0.5):
    """Choose the detected face that covers the Lightroom-labeled face region."""
    left, top, right, bottom = labeled_box(row, width, height)
    label_area = max(1.0, (right - left) * (bottom - top))
    best = None
    best_key = None
    for detection in detections:
        x0, y0, x1, y1 = detection["bbox"]
        overlap_width = max(0.0, min(right, x1) - max(left, x0))
        overlap_height = max(0.0, min(bottom, y1) - max(top, y0))
        coverage = overlap_width * overlap_height / label_area
        key = (coverage, detection.get("det_score", 0.0))
        if best_key is None or key > best_key:
            best, best_key = detection, key
    return best if best_key and best_key[0] >= minimum_coverage else None


def prepare_output(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [output_dir / name for name in ("reference-library.npz", "reference-library.json", "summary.json")]
    if any(path.exists() for path in existing):
        names = ", ".join(path.name for path in existing if path.exists())
        raise FileExistsError(f"Refusing to overwrite existing reference-library output: {names}")
    return output_dir


def build_reference_library(face_csv, output_dir, model_root, minimum_face_pixels=60):
    """Run one GPU face pass per source photo and persist accepted labeled embeddings."""
    from face_runtime import create_face_analysis

    output_dir = prepare_output(output_dir)
    grouped_rows = defaultdict(list)
    for row in read_face_rows(face_csv):
        grouped_rows[row["photo_path"]].append(row)

    app = create_face_analysis(model_root)
    entries = []
    embeddings = []
    counters = defaultdict(int)
    for photo_path, rows in grouped_rows.items():
        image = read_image(photo_path)
        if image is None:
            counters["unavailable_photos"] += 1
            continue
        height, width = image.shape[:2]
        faces = app.get(image)
        detections = [
            {"index": index, "bbox": face.bbox.tolist(), "det_score": float(face.det_score)}
            for index, face in enumerate(faces)
        ]
        for row in rows:
            detection = select_labeled_face(row, width, height, detections)
            if detection is None:
                counters["unmatched_labels"] += 1
                continue
            x0, y0, x1, y1 = detection["bbox"]
            if min(x1 - x0, y1 - y0) < minimum_face_pixels:
                counters["too_small_faces"] += 1
                continue
            embedding = np.asarray(faces[detection["index"]].embedding, dtype=np.float32)
            norm = np.linalg.norm(embedding)
            if not np.isfinite(norm) or norm == 0:
                counters["invalid_embeddings"] += 1
                continue
            embeddings.append(embedding / norm)
            entries.append(
                {
                    "person": row["person"],
                    "photo_path": photo_path,
                    "face_id": row.get("face_id", ""),
                    "bbox": [round(float(value), 2) for value in detection["bbox"]],
                    "det_score": round(detection["det_score"], 6),
                }
            )

    if not embeddings:
        raise RuntimeError("No labeled faces were accepted; verify source paths and face boxes.")
    matrix = np.stack(embeddings)
    np.savez_compressed(output_dir / "reference-library.npz", embeddings=matrix)
    (output_dir / "reference-library.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "people": len({entry["person"] for entry in entries}),
        "accepted_faces": len(entries),
        "embedding_dimension": int(matrix.shape[1]),
        "source_photos": len(grouped_rows),
        **dict(counters),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--faces-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model-root", required=True, type=Path)
    parser.add_argument("--minimum-face-pixels", type=int, default=60)
    args = parser.parse_args()
    summary = build_reference_library(
        args.faces_csv, args.output_dir, args.model_root, args.minimum_face_pixels
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
