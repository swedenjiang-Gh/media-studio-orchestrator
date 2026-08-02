"""Check the approved DirectShow capture device and actual signal level."""

import argparse
import locale
import re
import subprocess
import sys


DEFAULT_DEVICE = "CABLE Output (VB-Audio Virtual Cable)"


def _decode_ffmpeg_output(text):
    if isinstance(text, bytes):
        return text.decode(locale.getpreferredencoding(False), errors="replace")
    return text


def parse_dshow_audio_devices(text):
    """Extract DirectShow audio device names from FFmpeg device-list output."""
    text = _decode_ffmpeg_output(text)
    return re.findall(r'"(.+?)" \(audio\)', text)


def list_dshow_audio_devices(ffmpeg="ffmpeg"):
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        capture_output=True,
    )
    return parse_dshow_audio_devices(completed.stdout + completed.stderr)


def verify_signal(device=DEFAULT_DEVICE, duration=3.0, ffmpeg="ffmpeg", threshold_db=-55.0):
    """Record no file; measure whether the selected DirectShow device has usable signal."""
    completed = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostdin",
            "-t",
            str(duration),
            "-f",
            "dshow",
            "-i",
            f"audio={device}",
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
    )
    stderr = _decode_ffmpeg_output(completed.stderr)
    match = re.search(r"mean_volume: (-?[\d.]+) dB", stderr)
    mean_db = float(match.group(1)) if match else None
    return {
        "device": device,
        "available": device in list_dshow_audio_devices(ffmpeg),
        "mean_volume_db": mean_db,
        "has_signal": mean_db is not None and mean_db >= threshold_db,
        "ffmpeg_exit_code": completed.returncode,
    }


def main():
    parser = argparse.ArgumentParser(description="Check VB-CABLE DirectShow availability and signal.")
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.verify:
        print(verify_signal(args.device, args.duration, args.ffmpeg))
    else:
        print("\n".join(list_dshow_audio_devices(args.ffmpeg)))


if __name__ == "__main__":
    main()
