"""Detect visual change intervals from a complete, downscaled video timeline."""

import argparse
import json
import statistics
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np


def build_event_intervals(scores, fps, threshold, padding_seconds, merge_gap_seconds=1.0):
    """Group above-threshold frame changes into evidence intervals with a peak frame."""
    active = [index for index, score in enumerate(scores) if score >= threshold]
    if not active:
        return []

    max_gap_frames = round(merge_gap_seconds * fps)
    groups = [[active[0]]]
    for index in active[1:]:
        if index - groups[-1][-1] - 1 <= max_gap_frames:
            groups[-1].append(index)
        else:
            groups.append([index])

    intervals = []
    frame_seconds = 1.0 / fps
    for group in groups:
        peak_index = max(group, key=lambda index: scores[index])
        intervals.append(
            {
                "start": max(0.0, group[0] / fps - padding_seconds),
                "peak": peak_index / fps,
                "end": group[-1] / fps + frame_seconds + padding_seconds,
                "peak_score": scores[peak_index],
            }
        )
    merged = []
    for interval in intervals:
        if merged and interval["start"] <= merged[-1]["end"]:
            previous = merged[-1]
            previous["end"] = max(previous["end"], interval["end"])
            if interval["peak_score"] > previous["peak_score"]:
                previous["peak"] = interval["peak"]
                previous["peak_score"] = interval["peak_score"]
        else:
            merged.append(interval)
    return merged


def _video_shape(path, ffprobe):
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
    fps = float(Fraction(stream["avg_frame_rate"]))
    return stream["width"], stream["height"], fps


def build_scan_command(path, ffmpeg, scan_width, scan_height, scan_fps=None, hwaccel=None):
    """Build the FFmpeg command for a low-resolution visual change scan."""
    if hwaccel == "cuda":
        video_filter = f"scale_cuda={scan_width}:{scan_height},hwdownload,format=nv12,format=gray"
        command = [ffmpeg, "-hide_banner", "-nostdin", "-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
    else:
        video_filter = f"scale={scan_width}:{scan_height},format=gray"
        command = [ffmpeg, "-hide_banner", "-nostdin"]
    if scan_fps:
        video_filter += f",fps={scan_fps:g}"
    return command + [
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
        "gray",
        "pipe:1",
    ]


def scan_video(
    path,
    ffmpeg="ffmpeg",
    ffprobe="ffprobe",
    scan_width=160,
    padding_seconds=1.0,
    scan_fps=None,
    hwaccel=None,
):
    """Decode every video frame at low resolution and return visual-change event intervals."""
    source_width, source_height, fps = _video_shape(path, ffprobe)
    scan_height = max(2, round(scan_width * source_height / source_width / 2) * 2)
    frame_size = scan_width * scan_height
    if scan_fps is not None and scan_fps <= 0:
        raise ValueError("scan_fps must be positive")
    output_fps = scan_fps or fps
    command = build_scan_command(path, ffmpeg, scan_width, scan_height, scan_fps, hwaccel)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    previous = None
    scores = []
    try:
        while True:
            frame = process.stdout.read(frame_size)
            if len(frame) != frame_size:
                break
            current = np.frombuffer(frame, dtype=np.uint8)
            scores.append(0.0 if previous is None else float(np.abs(current.astype(np.int16) - previous).mean()))
            previous = current
    finally:
        if process.stdout:
            process.stdout.close()
        process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg event scan failed with exit code {process.returncode}")

    median = statistics.median(scores) if scores else 0.0
    deviations = [abs(score - median) for score in scores]
    threshold = median + max(5.0, 6.0 * (statistics.median(deviations) if deviations else 0.0))
    return {
        "source": str(Path(path).resolve()),
        "frames_scanned": len(scores),
        "scan_fps": output_fps,
        "threshold": threshold,
        "intervals": build_event_intervals(scores, fps, threshold, padding_seconds),
    }


def main():
    from list_media import write_manifest

    parser = argparse.ArgumentParser(description="Scan a whole video timeline for visual event intervals.")
    parser.add_argument("path")
    parser.add_argument("--output")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--scan-width", type=int, default=160)
    parser.add_argument("--scan-fps", type=float)
    parser.add_argument("--hwaccel", choices=["cuda"])
    parser.add_argument("--padding-seconds", type=float, default=1.0)
    args = parser.parse_args()
    result = scan_video(
        args.path,
        args.ffmpeg,
        args.ffprobe,
        args.scan_width,
        args.padding_seconds,
        args.scan_fps,
        args.hwaccel,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        write_manifest(result, sys.stdout)


if __name__ == "__main__":
    main()
