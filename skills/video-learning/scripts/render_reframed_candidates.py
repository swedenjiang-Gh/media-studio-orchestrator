"""Render separate 1080p viewing copies from 360 screening candidates."""

import argparse
import json
import subprocess
from pathlib import Path


def wrap_yaw(yaw):
    """Convert an unwrapped angle to FFmpeg's accepted yaw range."""
    return ((yaw + 180) % 360) - 180


def smooth_viewing_path(points):
    """Unwrap and locally smooth yaw values while retaining timestamped pitch values."""
    if not points:
        raise ValueError("viewing path must contain at least one point")
    ordered = sorted(points, key=lambda point: point["time"])
    result = []
    previous_yaw = None
    for point in ordered:
        yaw = float(point["yaw"])
        if previous_yaw is not None:
            yaw += 360 * round((previous_yaw - yaw) / 360)
        result.append({"time": float(point["time"]), "unwrapped_yaw": yaw, "pitch": float(point.get("pitch", 0))})
        previous_yaw = yaw
    if len(result) > 2:
        for index in range(1, len(result) - 1):
            result[index]["unwrapped_yaw"] = round(
                (result[index - 1]["unwrapped_yaw"] + 2 * result[index]["unwrapped_yaw"] + result[index + 1]["unwrapped_yaw"]) / 4,
                3,
            )
            result[index]["pitch"] = round(
                (result[index - 1]["pitch"] + 2 * result[index]["pitch"] + result[index + 1]["pitch"]) / 4,
                3,
            )
    return result


def interpolated_commands(path, interval_start, step_seconds=0.1):
    """Densify smooth path points so FFmpeg command changes remain visually gradual."""
    commands = []
    for left, right in zip(path, path[1:]):
        duration = right["time"] - left["time"]
        if duration <= 0:
            continue
        steps = max(1, round(duration / step_seconds))
        for index in range(steps):
            ratio = index / steps
            commands.append(
                {
                    "time": left["time"] + duration * ratio - interval_start,
                    "yaw": wrap_yaw(left["unwrapped_yaw"] + (right["unwrapped_yaw"] - left["unwrapped_yaw"]) * ratio),
                    "pitch": left["pitch"] + (right["pitch"] - left["pitch"]) * ratio,
                }
            )
    last = path[-1]
    commands.append({"time": last["time"] - interval_start, "yaw": wrap_yaw(last["unwrapped_yaw"]), "pitch": last["pitch"]})
    return commands


def write_rotation_commands(command_file, points, interval_start):
    """Write FFmpeg sendcmd instructions with times relative to the rendered candidate."""
    command_file = Path(command_file)
    smooth_path = smooth_viewing_path(points)
    lines = []
    for point in interpolated_commands(smooth_path, interval_start):
        time = max(0.0, point["time"])
        lines.append(f"{time:.3f} v360@viewer yaw {point['yaw']:.3f};")
        lines.append(f"{time:.3f} v360@viewer pitch {point['pitch']:.3f};")
    command_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def escape_filter_path(path):
    """Escape a Windows path used as an FFmpeg filter option value."""
    return str(Path(path)).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def build_reframe_command(source, start, end, command_file, target, ffmpeg="ffmpeg"):
    """Build a 1920x1080 H.265/AAC viewing-copy export with dynamic v360 rotation."""
    filter_graph = (
        f"[0:v:0]sendcmd=f='{escape_filter_path(command_file)}',"
        "v360@viewer=input=equirect:output=flat:yaw=0:pitch=0:h_fov=100:v_fov=75:w=1920:h=1080[view]"
    )
    return [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(source),
        "-t",
        f"{end - start:.3f}",
        "-filter_complex",
        filter_graph,
        "-map",
        "[view]",
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
        "-b:v",
        "20M",
        "-maxrate",
        "24M",
        "-c:a",
        "copy",
        str(target),
    ]


def render_candidates(source, candidates_json, output_dir, ffmpeg="ffmpeg"):
    """Render a reframed viewing copy for every candidate without overwriting existing files."""
    candidates = json.loads(Path(candidates_json).read_text(encoding="utf-8"))["candidates"]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for candidate in candidates:
        target = output_dir / f"candidate-{candidate['rank']:03d}-reframed.mp4"
        command_file = output_dir / f"candidate-{candidate['rank']:03d}-rotation.cmd"
        if target.exists() or command_file.exists():
            raise FileExistsError(f"Refusing to overwrite reframed output: {target}")
        write_rotation_commands(command_file, candidate["viewing_path"], candidate["start"])
        completed = subprocess.run(
            build_reframe_command(source, candidate["start"], candidate["end"], command_file, target, ffmpeg),
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"reframed export failed for {target}: {completed.stderr.decode('utf-8', errors='replace')[-1000:]}")
        rendered.append({"rank": candidate["rank"], "path": str(target), "rotation_commands": str(command_file)})
    return rendered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidates_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    print(json.dumps(render_candidates(args.source, args.candidates_json, args.output_dir, args.ffmpeg), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
