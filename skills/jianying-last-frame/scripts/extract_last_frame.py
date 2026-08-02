#!/usr/bin/env python3
"""Extract the final decoded frame of one video or all videos in a folder."""

from __future__ import annotations

import argparse
import fractions
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm")


def _load_imageio():
    try:
        import imageio.v2 as imageio  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: imageio. Install with: python -m pip install imageio imageio-ffmpeg"
        ) from exc

    try:
        import imageio_ffmpeg  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: imageio-ffmpeg. Install with: python -m pip install imageio-ffmpeg"
        ) from exc

    return imageio


def _default_output(video: Path) -> Path:
    return video.with_name(f"{video.stem}-last-frame.png")


def _find_binary(explicit: str | None, env_name: str, binary_name: str) -> str | None:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return str(path)
        found = shutil.which(explicit)
        if found:
            return found
        raise FileNotFoundError(f"{binary_name} not found: {explicit}")
    env_value = os.getenv(env_name)
    if env_value:
        return _find_binary(env_value, env_name, binary_name)
    return shutil.which(binary_name)


def _parse_rate(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    try:
        return float(fractions.Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def _probe_metadata(video: Path, ffprobe: str | None) -> dict[str, Any]:
    if not ffprobe:
        return {}
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,nb_frames,duration:format=duration",
        "-of",
        "json",
        str(video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        return {"probe_error": result.stderr.strip() or result.stdout.strip()}
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"probe_error": "ffprobe returned invalid JSON"}

    stream = (data.get("streams") or [{}])[0]
    format_data = data.get("format") or {}
    duration = stream.get("duration") or format_data.get("duration")
    nb_frames = stream.get("nb_frames")
    return {
        "fps": _parse_rate(stream.get("avg_frame_rate")),
        "duration": float(duration) if duration not in (None, "N/A") else None,
        "size": [stream.get("width"), stream.get("height")]
        if stream.get("width") and stream.get("height")
        else None,
        "frames": int(nb_frames) if nb_frames and str(nb_frames).isdigit() else None,
    }


def _run_ffmpeg_extract(video: Path, output: Path, ffmpeg: str) -> None:
    # Seek near the end, decode to EOF, and keep overwriting the same image so
    # the final write is the final decoded frame. Fall back to full decode for
    # very short files or containers that cannot seek from EOF.
    common = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    tail_cmd = [
        *common,
        "-sseof",
        "-1",
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-an",
        "-fps_mode",
        "passthrough",
        "-update",
        "1",
        "-y",
        str(output),
    ]
    full_cmd = [
        *common,
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-an",
        "-fps_mode",
        "passthrough",
        "-update",
        "1",
        "-y",
        str(output),
    ]
    result = subprocess.run(tail_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode == 0 and output.is_file():
        return
    fallback = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if fallback.returncode != 0 or not output.is_file():
        message = fallback.stderr.strip() or result.stderr.strip() or "ffmpeg did not write output"
        raise RuntimeError(message)


def _extract_with_imageio(video: Path, output: Path) -> dict[str, Any]:
    imageio = _load_imageio()

    reader = imageio.get_reader(str(video), "ffmpeg")
    last_frame = None
    frame_count = 0
    try:
        meta = reader.get_meta_data()
        for frame in reader:
            last_frame = frame
            frame_count += 1
    finally:
        reader.close()

    if last_frame is None:
        raise RuntimeError(f"No video frame decoded: {video}")

    imageio.imwrite(str(output), last_frame)
    return {
        "backend": "imageio-ffmpeg",
        "frames": frame_count,
        "fps": meta.get("fps"),
        "duration": meta.get("duration"),
        "size": meta.get("size"),
    }


def extract_last_frame(
    video: Path,
    output: Path,
    overwrite: bool = True,
    backend: str = "auto",
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
) -> dict[str, Any]:
    if not video.is_file():
        raise FileNotFoundError(f"Video not found: {video}")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output exists: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_path = _find_binary(ffmpeg, "FFMPEG_BINARY", "ffmpeg")
    ffprobe_path = _find_binary(ffprobe, "FFPROBE_BINARY", "ffprobe")
    if backend not in {"auto", "ffmpeg", "imageio"}:
        raise ValueError(f"Unsupported backend: {backend}")

    metadata: dict[str, Any] = {}
    if backend in {"auto", "ffmpeg"} and ffmpeg_path:
        _run_ffmpeg_extract(video, output, ffmpeg_path)
        metadata = _probe_metadata(video, ffprobe_path)
        metadata["backend"] = "ffmpeg"
        metadata["ffmpeg"] = ffmpeg_path
        if ffprobe_path:
            metadata["ffprobe"] = ffprobe_path
    elif backend == "ffmpeg":
        raise FileNotFoundError("ffmpeg not found. Put it on PATH or pass --ffmpeg.")
    else:
        metadata = _extract_with_imageio(video, output)

    return {
        "source": str(video),
        "output": str(output),
        "bytes": os.path.getsize(output),
        **metadata,
    }


def iter_videos(input_dir: Path, recursive: bool, extensions: Iterable[str]) -> list[Path]:
    wanted = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
    paths = input_dir.rglob("*") if recursive else input_dir.iterdir()
    return sorted(p for p in paths if p.is_file() and p.suffix.lower() in wanted)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", help="Input video path.")
    source.add_argument("--input-dir", help="Folder containing videos to process.")
    parser.add_argument("--output", help="Output image path for --video. Defaults to <video-stem>-last-frame.png.")
    parser.add_argument("--output-dir", help="Output folder for --input-dir. Defaults to <input-dir>/last-frames.")
    parser.add_argument("--recursive", action="store_true", help="Search input directory recursively.")
    parser.add_argument(
        "--extensions",
        default=",".join(VIDEO_EXTENSIONS),
        help="Comma-separated video extensions for --input-dir.",
    )
    parser.add_argument("--backend", choices=("auto", "ffmpeg", "imageio"), default="auto")
    parser.add_argument("--ffmpeg", help="Path or command name for ffmpeg.")
    parser.add_argument("--ffprobe", help="Path or command name for ffprobe.")
    parser.add_argument("--no-overwrite", action="store_true", help="Fail if the output already exists.")
    args = parser.parse_args()

    if args.video:
        video = Path(args.video).expanduser().resolve()
        output = Path(args.output).expanduser().resolve() if args.output else _default_output(video)
        result: Any = extract_last_frame(
            video,
            output,
            overwrite=not args.no_overwrite,
            backend=args.backend,
            ffmpeg=args.ffmpeg,
            ffprobe=args.ffprobe,
        )
    else:
        input_dir = Path(args.input_dir).expanduser().resolve()
        if not input_dir.is_dir():
            raise NotADirectoryError(f"Input directory not found: {input_dir}")
        output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else input_dir / "last-frames"
        extensions = [part.strip() for part in args.extensions.split(",") if part.strip()]
        videos = iter_videos(input_dir, args.recursive, extensions)
        result = []
        for video in videos:
            output = output_dir / f"{video.stem}-last-frame.png"
            result.append(
                extract_last_frame(
                    video,
                    output,
                    overwrite=not args.no_overwrite,
                    backend=args.backend,
                    ffmpeg=args.ffmpeg,
                    ffprobe=args.ffprobe,
                )
            )
        result = {"count": len(result), "outputs": result}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
