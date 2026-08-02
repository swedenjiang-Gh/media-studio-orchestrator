"""Inspect local media and conservatively classify Insta360 inputs."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def classify_insta360(path, probe):
    """Classify only a clearly tagged equirectangular INSV as directly analyzable."""
    is_insv = Path(path).suffix.lower() == ".insv"
    video_streams = [item for item in probe.get("streams", []) if item.get("codec_type") == "video"]
    is_equirectangular = any(
        item.get("tags", {}).get("projection", "").lower() == "equirectangular"
        for item in video_streams
    )
    if is_insv and is_equirectangular:
        return {"kind": "stitched_360", "requires_studio_export": False}
    if is_insv:
        return {"kind": "raw_or_unknown_insv", "requires_studio_export": True}
    return {"kind": "standard_media", "requires_studio_export": False}


def ffprobe_json(path, ffprobe="ffprobe"):
    """Return stream metadata without decoding or modifying media."""
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,avg_frame_rate:stream_tags=projection,stereo_mode",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


def inspect(path, ffprobe="ffprobe"):
    probe = ffprobe_json(path, ffprobe)
    return {"path": str(Path(path).resolve()), "probe": probe, "classification": classify_insta360(path, probe)}


def main():
    from list_media import write_manifest

    parser = argparse.ArgumentParser(description="Inspect media and classify Insta360 INSV files.")
    parser.add_argument("path")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    write_manifest(inspect(args.path, args.ffprobe), sys.stdout)


if __name__ == "__main__":
    main()
