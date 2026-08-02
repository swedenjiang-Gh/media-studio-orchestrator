"""Stitch each raw Insta360 INSV in a folder, then run the verified batch screening route."""

import argparse
import json
import subprocess
from pathlib import Path


def list_insv_sources(folder):
    """Return raw Insta360 sources recursively in stable path order."""
    folder = Path(folder)
    return sorted(
        (path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".insv"),
        key=lambda path: str(path).lower(),
    )


def safe_slug(path):
    """Return a filesystem-safe output name based on the source stem."""
    import re

    return re.sub(r"[^0-9A-Za-z._-]+", "-", Path(path).stem).strip(".-") or "insv"


def build_full_export_command(demo_exe, sdk_root, source, output):
    """Build the full-export command verified with the official Windows demo."""
    return [
        str(demo_exe),
        "-inputs", str(source),
        "-output", str(output),
        "-model_root_dir", str(Path(sdk_root) / "models"),
        "-stitch_type", "aistitch",
        "-bitrate", "60000000",
        "-enable_flowstate", "ON",
        "-output_size", "3840x1920",
        "-enable_h265_encoder", "h265",
        "-disable_cuda", "false",
    ]


def run_full_export(source, output, sdk_root, demo_exe):
    """Export one independent 2:1 equirectangular master without overwriting it."""
    from insta360_sdk_frames import build_runtime_env

    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite stitched output: {output}")
    command = build_full_export_command(demo_exe, sdk_root, source, output)
    subprocess.run(command, env=build_runtime_env(sdk_root), check=True)
    if not output.is_file():
        raise RuntimeError(f"Official MediaSDK demo completed without creating: {output}")


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resume_screening_root(output_root):
    """Choose a new screening directory instead of replacing an interrupted delivery."""
    primary = Path(output_root) / "screening"
    if not primary.exists():
        return primary
    index = 1
    while True:
        candidate = Path(output_root) / f"screening-resume-{index:03d}"
        if not candidate.exists():
            return candidate
        index += 1


def run_folder(
    folder,
    output_root,
    sdk_root,
    demo_exe,
    reference_dir,
    model_root,
    threshold,
    dialogue_model=None,
    ffmpeg="ffmpeg",
    ffprobe="ffprobe",
    stitcher=run_full_export,
    batch_runner=None,
    inspect_fn=None,
    resume=False,
):
    """Stitch eligible INSV files sequentially and pass only usable sources to batch screening."""
    from inspect_media import inspect
    from screen_video_batch import run_batch

    folder = Path(folder)
    output_root = Path(output_root)
    if not folder.is_dir():
        raise ValueError(f"Insta360 source folder not found: {folder}")
    if output_root.exists() and not resume:
        raise FileExistsError(f"Refusing to reuse an existing output root: {output_root}")
    sources = list_insv_sources(folder)
    if not sources:
        raise ValueError(f"No .insv files found under: {folder}")
    output_root.mkdir(parents=True, exist_ok=resume)
    stitched_dir = output_root / "stitched"
    stitched_dir.mkdir(exist_ok=resume)
    inspect_fn = inspect if inspect_fn is None else inspect_fn
    batch_runner = run_batch if batch_runner is None else batch_runner
    records = []
    downstream_sources = []
    screening = {"jobs": []}
    screening_root = resume_screening_root(output_root) if resume else output_root / "screening"

    def snapshot():
        manifest = {
            "source_folder": str(folder),
            "sources": records,
            "screening_root": str(screening_root),
            "screening": screening,
        }
        write_json(output_root / "insta360-folder-manifest.json", manifest)
        return manifest

    snapshot()

    for index, source in enumerate(sources, start=1):
        record = {"source": str(source), "sdk_status": "queued", "stitched_output": None, "screening_status": "not_started"}
        try:
            inspection = inspect_fn(source, ffprobe=ffprobe)
            record["classification"] = inspection["classification"]["kind"]
            if record["classification"] == "stitched_360":
                output = source
                record["sdk_status"] = "not_required_already_stitched"
            else:
                output = stitched_dir / f"{index:03d}-{safe_slug(source)}_360.mp4"
                if resume and output.is_file():
                    record["sdk_status"] = "reused_existing_stitched_output"
                else:
                    stitcher(source, output, sdk_root=sdk_root, demo_exe=demo_exe)
                    record["sdk_status"] = "complete"
            record["stitched_output"] = str(output)
            downstream_sources.append(Path(output))
        except Exception as error:
            record["sdk_status"] = "blocked"
            record["error"] = str(error)
        records.append(record)
        snapshot()

    if downstream_sources:
        screening = batch_runner(
            downstream_sources,
            screening_root,
            reference_dir=reference_dir,
            model_root=model_root,
            threshold=threshold,
            dialogue_model=dialogue_model,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
        )
        statuses = {str(job["source"]): job["status"] for job in screening["jobs"]}
        for record in records:
            if record["stitched_output"]:
                record["screening_status"] = statuses.get(record["stitched_output"], "blocked_missing_batch_job")

    return snapshot()


def validate_sdk(sdk_root, demo_exe):
    """Reject incomplete SDK configuration before any source processing starts."""
    sdk_root = Path(sdk_root)
    demo_exe = Path(demo_exe)
    if not demo_exe.is_file():
        raise ValueError(f"Official MediaSDK demo executable not found: {demo_exe}")
    if not (sdk_root / "models").is_dir() or not (sdk_root / "bin").is_dir():
        raise ValueError(f"MediaSDK root must contain models and bin directories: {sdk_root}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--sdk-root", required=True, type=Path)
    parser.add_argument("--demo-exe", required=True, type=Path)
    parser.add_argument("--reference-dir", required=True, type=Path)
    parser.add_argument("--model-root", required=True, type=Path)
    parser.add_argument("--threshold", required=True, type=float)
    parser.add_argument("--dialogue-model", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--resume", action="store_true", help="Reuse completed stitched masters and create a new screening subdirectory.")
    args = parser.parse_args()

    validate_sdk(args.sdk_root, args.demo_exe)
    print(json.dumps(
        run_folder(
            args.folder, args.output_root, args.sdk_root, args.demo_exe, args.reference_dir,
            args.model_root, args.threshold, args.dialogue_model, args.ffmpeg, args.ffprobe, resume=args.resume,
        ),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
