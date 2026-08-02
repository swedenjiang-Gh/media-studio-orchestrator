"""Expand local video files and folders into a stable batch manifest."""

import argparse
import json
import sys
from pathlib import Path


VIDEO_SUFFIXES = {".avi", ".insv", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"}


def collect_media_paths(input_paths):
    """Return recursive video files, missing inputs, and ignored local files."""
    media = {}
    missing = []
    ignored = []

    for raw_path in input_paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            missing.append(str(path))
        elif path.is_file():
            if path.suffix.lower() in VIDEO_SUFFIXES:
                media[str(path).casefold()] = str(path)
            else:
                ignored.append(str(path))
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in VIDEO_SUFFIXES:
                    resolved = candidate.resolve()
                    media[str(resolved).casefold()] = str(resolved)

    return {
        "media": [media[key] for key in sorted(media)],
        "missing": sorted(set(missing), key=str.casefold),
        "ignored": sorted(set(ignored), key=str.casefold),
    }


def write_manifest(manifest, stream):
    """Write JSON without losing non-ASCII filenames on Windows consoles."""
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")
    stream.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="List supported local videos from files and folders."
    )
    parser.add_argument("paths", nargs="+", help="Local video files or folders")
    args = parser.parse_args()
    write_manifest(collect_media_paths(args.paths), sys.stdout)


if __name__ == "__main__":
    main()
