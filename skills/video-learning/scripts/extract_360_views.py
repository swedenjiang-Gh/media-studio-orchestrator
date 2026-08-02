"""Extract rectilinear evidence views from a stitched equirectangular 360 video."""

import argparse
import json
import subprocess
from pathlib import Path


HORIZON_VIEWS = {
    "front": (0, 0),
    "right": (90, 0),
    "back": (180, 0),
    "left": (-90, 0),
}
VERTICAL_VIEWS = {"up": (0, 90), "down": (0, -90)}


def v360_filter(view, width, height):
    """Return the verified FFmpeg v360 filter for one evidence view."""
    yaw, pitch = {**HORIZON_VIEWS, **VERTICAL_VIEWS}[view]
    return (
        "v360=input=equirect:output=flat:"
        f"yaw={yaw}:pitch={pitch}:h_fov=100:v_fov=75:w={width}:h={height}"
    )


def build_view_manifest(intervals, output_dir, include_vertical=False):
    """Create ordered start/peak/end targets for overlapping 360 evidence views."""
    output = Path(output_dir)
    views = {**HORIZON_VIEWS, **(VERTICAL_VIEWS if include_vertical else {})}
    frames = []
    for index, interval in enumerate(intervals, start=1):
        event_id = f"event-{index:03d}"
        for role in ("start", "peak", "end"):
            for view in views:
                frames.append(
                    {
                        "event_id": event_id,
                        "role": role,
                        "view": view,
                        "time": interval[role],
                        "path": str(output / f"{event_id}-{role}-{view}.jpg").replace("\\", "/"),
                    }
                )
    return frames


def extract_360_views(video, intervals, output_dir, width=1280, height=720, include_vertical=False, ffmpeg="ffmpeg"):
    """Extract 360 evidence views without overwriting existing files."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    frames = build_view_manifest(intervals, output, include_vertical)
    for frame in frames:
        target = Path(frame["path"])
        if target.exists():
            frame["status"] = "existing"
            continue
        completed = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-nostdin",
                "-ss",
                str(frame["time"]),
                "-i",
                str(video),
                "-map",
                "0:v:0",
                "-vf",
                v360_filter(frame["view"], width, height),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                "-update",
                "1",
                str(target),
            ],
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"ffmpeg 360 frame extraction failed for {target}")
        frame["status"] = "created"
    return frames


def main():
    parser = argparse.ArgumentParser(description="Extract overlapping evidence views from a stitched 360 video.")
    parser.add_argument("video")
    parser.add_argument("events_json")
    parser.add_argument("output_dir")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--vertical", action="store_true")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    intervals = json.loads(Path(args.events_json).read_text(encoding="utf-8"))["intervals"]
    result = extract_360_views(
        args.video,
        intervals,
        args.output_dir,
        args.width,
        args.height,
        args.vertical,
        args.ffmpeg,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
