"""Extract start, peak, and end evidence frames for detected video events."""

import argparse
import json
import subprocess
from pathlib import Path


def event_frame_manifest(intervals, output_dir):
    """Return deterministic evidence-frame targets for ordered event intervals."""
    output = Path(output_dir)
    frames = []
    for index, interval in enumerate(intervals, start=1):
        event_id = f"event-{index:03d}"
        for role in ("start", "peak", "end"):
            frames.append(
                {
                    "event_id": event_id,
                    "role": role,
                    "time": interval[role],
                    "path": str(output / f"{event_id}-{role}.jpg").replace("\\", "/"),
                }
            )
    return frames


def extract_event_frames(video, intervals, output_dir, ffmpeg="ffmpeg"):
    """Create evidence frames without overwriting existing output files."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    frames = event_frame_manifest(intervals, output)
    for frame in frames:
        target = Path(frame["path"])
        if target.exists():
            frame["status"] = "existing"
            continue
        command = [
            ffmpeg,
            "-hide_banner",
            "-nostdin",
            "-ss",
            str(frame["time"]),
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-q:v",
            "2",
            "-update",
            "1",
            str(target),
        ]
        completed = subprocess.run(command, capture_output=True)
        if completed.returncode != 0:
            raise RuntimeError(f"ffmpeg frame extraction failed for {target}")
        frame["status"] = "created"
    return frames


def main():
    parser = argparse.ArgumentParser(description="Extract start, peak, and end frames for event intervals.")
    parser.add_argument("video")
    parser.add_argument("events_json")
    parser.add_argument("output_dir")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    intervals = json.loads(Path(args.events_json).read_text(encoding="utf-8"))["intervals"]
    result = extract_event_frames(args.video, intervals, args.output_dir, args.ffmpeg)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
