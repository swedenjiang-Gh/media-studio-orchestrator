"""Scan a flat video with the local CUDA face model and Lightroom reference library."""

import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np

from face_candidates import group_face_samples, score_people
from face_runtime import create_face_analysis


def build_scan_command(path, ffmpeg, width, sample_fps):
    """Build a CUDA decode command that only transfers sampled, reduced frames to Python."""
    return [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-hwaccel",
        "cuda",
        "-hwaccel_output_format",
        "cuda",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        f"fps={sample_fps:g},scale_cuda={width}:-2,hwdownload,format=nv12,format=bgr24",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "pipe:1",
    ]


def identity_result(scores, threshold):
    """Return a review-only name candidate; no score alone confirms identity."""
    person, score = max(scores.items(), key=lambda item: item[1])
    return {
        "person": person,
        "score": round(float(score), 6),
        "status": "review_candidate" if score >= threshold else "unverified",
    }


def load_reference(reference_dir):
    reference_dir = Path(reference_dir)
    archive = np.load(reference_dir / "reference-library.npz")
    entries = json.loads((reference_dir / "reference-library.json").read_text(encoding="utf-8"))
    embeddings = archive["embeddings"]
    if len(embeddings) != len(entries):
        raise ValueError("reference library embeddings and metadata do not have equal lengths")
    return embeddings, [entry["person"] for entry in entries]


def video_shape(path, ffprobe):
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,avg_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    stream = json.loads(completed.stdout)["streams"][0]
    return stream["width"], stream["height"], float(Fraction(stream["avg_frame_rate"]))


def scan_known_faces(video, reference_dir, model_root, width=1280, sample_fps=2.0, threshold=0.65,
                     ffmpeg="ffmpeg", ffprobe="ffprobe"):
    """Return sampled face evidence and continuous named review candidates for one flat video."""
    source_width, source_height, _ = video_shape(video, ffprobe)
    height = max(2, round(width * source_height / source_width / 2) * 2)
    embeddings, people = load_reference(reference_dir)
    app = create_face_analysis(model_root)
    process = subprocess.Popen(
        build_scan_command(video, ffmpeg, width, sample_fps),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    frame_size = width * height * 3
    samples = []
    interval_samples = []
    try:
        index = 0
        while True:
            raw = process.stdout.read(frame_size)
            if len(raw) != frame_size:
                break
            frame = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3)
            time = index / sample_fps
            faces = []
            for face in app.get(frame):
                x0, y0, x1, y1 = (float(value) for value in face.bbox)
                face_pixels = round(min(x1 - x0, y1 - y0), 2)
                identity = identity_result(score_people(face.embedding, embeddings, people), threshold)
                result = {
                    "bbox": [round(value, 2) for value in (x0, y0, x1, y1)],
                    "det_score": round(float(face.det_score), 6),
                    "face_pixels": face_pixels,
                    "fully_inside_frame": x0 >= 2 and y0 >= 2 and x1 <= width - 2 and y1 <= height - 2,
                    "identity": identity,
                }
                faces.append(result)
                if identity["status"] == "review_candidate" and result["fully_inside_frame"]:
                    interval_samples.append(
                        {
                            "time": time,
                            "person": identity["person"],
                            "score": identity["score"],
                            "face_pixels": face_pixels,
                        }
                    )
            samples.append({"time": time, "faces": faces})
            index += 1
    finally:
        if process.stdout:
            process.stdout.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg known-face scan failed with exit code {process.returncode}: {stderr[-1000:]}")
    return {
        "source": str(Path(video).resolve()),
        "scan_width": width,
        "scan_height": height,
        "sample_fps": sample_fps,
        "threshold": threshold,
        "samples": samples,
        "review_candidates": group_face_samples(interval_samples, 1.5 / sample_fps, 1.0 / sample_fps),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--reference-dir", required=True, type=Path)
    parser.add_argument("--model-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--sample-fps", type=float, default=2.0)
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing known-face scan: {args.output}")
    result = scan_known_faces(
        args.video, args.reference_dir, args.model_root, args.width, args.sample_fps,
        args.threshold, args.ffmpeg, args.ffprobe,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"samples": len(result["samples"]), "review_candidates": len(result["review_candidates"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
