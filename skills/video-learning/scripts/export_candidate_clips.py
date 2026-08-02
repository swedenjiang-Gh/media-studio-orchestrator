"""Export padded, time-bounded candidate clips without modifying the source video."""

import argparse
import json
import subprocess
from pathlib import Path


def clip_bounds(interval, duration, padding):
    """Return a padded source interval constrained to the available duration."""
    return max(0.0, float(interval["start"]) - padding), min(duration, float(interval["end"]) + padding)


def build_clip_command(source, start, end, target, ffmpeg="ffmpeg", equirectangular=True):
    """Build an accurate GPU re-encode command that preserves optional audio."""
    command = [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(source),
        "-t",
        f"{end - start:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "hevc_nvenc",
        "-preset",
        "p7",
        "-tune",
        "hq",
        "-rc",
        "vbr",
        "-cq",
        "19",
        "-b:v",
        "0",
        "-c:a",
        "copy",
    ]
    if equirectangular:
        command += ["-metadata:s:v:0", "projection=equirectangular"]
    return command + [str(target)]


def source_duration(source, ffprobe="ffprobe"):
    completed = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(source)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(json.loads(completed.stdout)["format"]["duration"])


def candidate_intervals(data):
    """Read intervals from legacy face/event manifests or the ranked screening manifest."""
    if isinstance(data, list):
        return data
    intervals = data.get("candidates", data.get("review_candidates", data.get("intervals")))
    if not isinstance(intervals, list):
        raise ValueError("candidate manifest must be a list or contain candidates/review_candidates/intervals")
    return intervals


def export_candidates(source, candidates_json, output_dir, padding=1.0, ffmpeg="ffmpeg", ffprobe="ffprobe", equirectangular=True):
    """Export all candidate intervals from a manifest into a new directory."""
    data = json.loads(Path(candidates_json).read_text(encoding="utf-8"))
    intervals = candidate_intervals(data)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = source_duration(source, ffprobe)
    exported = []
    for index, interval in enumerate(intervals, start=1):
        start, end = clip_bounds(interval, duration, padding)
        target = output_dir / f"candidate-{index:03d}-{start:010.3f}-{end:010.3f}.mp4"
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing candidate clip: {target}")
        completed = subprocess.run(
            build_clip_command(source, start, end, target, ffmpeg, equirectangular), capture_output=True
        )
        if completed.returncode != 0:
            raise RuntimeError(f"candidate clip export failed for {target}")
        exported.append({"source_interval": {"start": start, "end": end}, "path": str(target)})
    return exported


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidates_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--padding", type=float, default=1.0)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    result = export_candidates(
        args.source, args.candidates_json, args.output_dir, args.padding, args.ffmpeg, args.ffprobe
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
