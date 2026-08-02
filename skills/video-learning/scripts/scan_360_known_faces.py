"""Scan overlapping flat views from a stitched 360 video for review-only face candidates."""

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from face_candidates import group_face_samples
from face_runtime import create_face_analysis
from scan_known_faces import identity_result, load_reference


HORIZON_VIEWS = {"front": 0, "right": 90, "back": 180, "left": -90}


def view_height(width):
    """Return an even 16:9 projection height."""
    return max(2, round(width * 9 / 16 / 2) * 2)


def build_view_scan_command(path, view, ffmpeg, width, sample_fps):
    """Build a GPU-decoded, CPU-projected FFmpeg command for one 360 horizon view."""
    if view not in HORIZON_VIEWS:
        raise ValueError(f"unsupported 360 view: {view}")
    height = view_height(width)
    video_filter = (
        "hwdownload,format=nv12,"
        f"v360=input=equirect:output=flat:yaw={HORIZON_VIEWS[view]}:pitch=0:"
        f"h_fov=100:v_fov=75:w={width}:h={height},fps={sample_fps:g},format=bgr24"
    )
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
        video_filter,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "pipe:1",
    ]


def group_view_face_samples(samples, max_gap_seconds, sample_interval_seconds):
    """Group review-level face samples without joining separate view directions."""
    grouped = []
    for view in HORIZON_VIEWS:
        view_samples = [sample for sample in samples if sample["view"] == view]
        for interval in group_face_samples(view_samples, max_gap_seconds, sample_interval_seconds):
            interval["view"] = view
            grouped.append(interval)
    return sorted(grouped, key=lambda interval: (interval["person"], interval["view"], interval["start"]))


def open_view_scan(command):
    """Stream raw frames without allowing FFmpeg diagnostics to block a long scan."""
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def scan_360_known_faces(video, reference_dir, model_root, width=1280, sample_fps=2.0, threshold=0.65,
                         ffmpeg="ffmpeg"):
    """Return face evidence across four overlapping 360 views without confirming identities."""
    embeddings, people = load_reference(reference_dir)
    app = create_face_analysis(model_root)
    height = view_height(width)
    frame_size = width * height * 3
    samples = []
    review_samples = []
    for view in HORIZON_VIEWS:
        process = open_view_scan(build_view_scan_command(video, view, ffmpeg, width, sample_fps))
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
                    identity = identity_result(
                        {person: float(score) for person, score in _score_people(face.embedding, embeddings, people).items()},
                        threshold,
                    )
                    result = {
                        "bbox": [round(value, 2) for value in (x0, y0, x1, y1)],
                        "det_score": round(float(face.det_score), 6),
                        "face_pixels": face_pixels,
                        "fully_inside_frame": x0 >= 2 and y0 >= 2 and x1 <= width - 2 and y1 <= height - 2,
                        "identity": identity,
                    }
                    faces.append(result)
                    if identity["status"] == "review_candidate" and result["fully_inside_frame"]:
                        review_samples.append(
                            {
                                "time": time,
                                "view": view,
                                "person": identity["person"],
                                "score": identity["score"],
                                "face_pixels": face_pixels,
                            }
                        )
                samples.append({"time": time, "view": view, "faces": faces})
                index += 1
        finally:
            if process.stdout:
                process.stdout.close()
            process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg 360 known-face scan failed for {view}: exit code {process.returncode}")
    return {
        "source": str(Path(video).resolve()),
        "views": list(HORIZON_VIEWS),
        "scan_width": width,
        "scan_height": height,
        "sample_fps": sample_fps,
        "threshold": threshold,
        "samples": samples,
        "review_candidates": group_view_face_samples(review_samples, 1.5 / sample_fps, 1.0 / sample_fps),
    }


def _score_people(embedding, reference_embeddings, reference_people):
    from face_candidates import score_people

    return score_people(embedding, reference_embeddings, reference_people)


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
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing 360 known-face scan: {args.output}")
    result = scan_360_known_faces(
        args.video, args.reference_dir, args.model_root, args.width, args.sample_fps,
        args.threshold, args.ffmpeg,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"samples": len(result["samples"]), "review_candidates": len(result["review_candidates"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
