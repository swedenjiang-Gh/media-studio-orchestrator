"""Export selected stitched 360 frames from raw Insta360 media via the official Media SDK demo."""

import argparse
import json
import os
import subprocess
from pathlib import Path


DEFAULT_SDK_ROOT = (
    "D:/CodexVideoLearning/tools/insta360-desktop-media-sdk/MediaSDK-3.1.3/"
    "MediaSDK-3.1.3-20260128-win64/MediaSDK"
)
DEFAULT_DEMO_EXE = "D:/CodexVideoLearning/work/insta360-sdk-validation/official-demo/MediaSDKDemo.exe"


def parse_output_size(value):
    try:
        width_text, height_text = value.lower().split("x")
        width, height = int(width_text), int(height_text)
    except (AttributeError, ValueError) as error:
        raise ValueError("output size must be WIDTHxHEIGHT, for example 3840x1920") from error
    if width <= 0 or height <= 0 or width != height * 2:
        raise ValueError("output size must be a positive 2:1 equirectangular size")
    return width, height


def build_runtime_env(sdk_root, environment=None):
    result = dict(os.environ if environment is None else environment)
    sdk_bin = str(Path(sdk_root) / "bin")
    current_path = result.get("PATH", "")
    result["PATH"] = sdk_bin if not current_path else sdk_bin + os.pathsep + current_path
    return result


def build_command(demo_exe, sdk_root, inputs, output_dir, frame_numbers, output_size, stitch_type):
    return [
        str(demo_exe),
        "-inputs",
        *(str(path) for path in inputs),
        "-image_sequence_dir",
        str(output_dir),
        "-export_frame_index",
        "-".join(str(frame) for frame in frame_numbers),
        "-model_root_dir",
        str(Path(sdk_root) / "models"),
        "-output_size",
        output_size,
        "-stitch_type",
        stitch_type,
    ]


def require_existing_file(path, description):
    resolved = Path(path)
    if not resolved.is_file():
        raise ValueError(f"{description} not found: {resolved}")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, help="One or two source .insv paths.")
    parser.add_argument("--output-dir", required=True, help="Existing or new output directory for JPEG frames.")
    parser.add_argument("--frames", nargs="+", required=True, type=int, help="Zero-based source frame indices.")
    parser.add_argument("--output-size", default="3840x1920")
    parser.add_argument("--stitch-type", default="optflow", choices=["template", "optflow", "dynamicstitch", "aistitch"])
    parser.add_argument("--sdk-root", default=os.environ.get("INSTA360_MEDIA_SDK_ROOT", DEFAULT_SDK_ROOT))
    parser.add_argument("--demo-exe", default=os.environ.get("INSTA360_MEDIA_SDK_DEMO", DEFAULT_DEMO_EXE))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    parse_output_size(args.output_size)
    if any(frame < 0 for frame in args.frames):
        raise ValueError("frame indices must be zero or greater")
    sdk_root = Path(args.sdk_root)
    require_existing_file(args.demo_exe, "official MediaSDK demo executable")
    if not (sdk_root / "models").is_dir() or not (sdk_root / "bin").is_dir():
        raise ValueError(f"MediaSDK root must contain models and bin directories: {sdk_root}")
    inputs = [require_existing_file(path, "source input") for path in args.inputs]
    output_dir = Path(args.output_dir)
    command = build_command(
        args.demo_exe,
        sdk_root,
        inputs,
        output_dir,
        args.frames,
        args.output_size,
        args.stitch_type,
    )
    if args.dry_run:
        print(json.dumps({"command": command, "output_dir": str(output_dir)}, ensure_ascii=False, indent=2))
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    existing_outputs = [output_dir / f"{frame}.jpg" for frame in args.frames]
    collisions = [str(path) for path in existing_outputs if path.exists()]
    if collisions:
        raise ValueError("refusing to overwrite existing frame output(s): " + ", ".join(collisions))
    subprocess.run(command, env=build_runtime_env(sdk_root), check=True)
    print(json.dumps({"inputs": [str(path) for path in inputs], "output_dir": str(output_dir), "frames": args.frames}, ensure_ascii=False))


if __name__ == "__main__":
    main()
