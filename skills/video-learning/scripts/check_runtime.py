"""Report local video-learning tool readiness without changing the machine."""

import importlib.util
import json
import os
import shutil
from pathlib import Path


EXECUTABLES = ("ffmpeg", "ffprobe", "yt-dlp", "tesseract")
PACKAGES = ("faster_whisper", "pytesseract")
DEFAULT_WORKSPACE = Path(r"D:\CodexVideoLearning")


def workspace_root():
    """Return the configured local runtime root without changing machine state."""
    return Path(os.environ.get("VIDEO_LEARNING_ROOT", DEFAULT_WORKSPACE))


def configured_runtime(root=None):
    """Report the approved workstation-local tools without changing state."""
    root = workspace_root() if root is None else Path(root)
    return {
        "workspace": root.is_dir(),
        "venv_python": (root / "venv" / "Scripts" / "python.exe").is_file(),
        "yt_dlp": (root / "bin" / "yt-dlp.exe").is_file(),
        "tesseract": (root / "Tesseract-OCR" / "tesseract.exe").is_file(),
        "vision_runner": (root / "vision" / "runtime" / "llama-mtmd-cli.exe").is_file(),
        "vision_model": (
            root / "vision" / "models" / "Qwen2.5-VL-7B-Instruct-Q8_0.gguf"
        ).is_file(),
        "vision_projector": (root / "vision" / "models" / "mmproj-F16.gguf").is_file(),
    }


def probe(executable_names, package_names, which=shutil.which, find_spec=importlib.util.find_spec):
    """Return boolean availability for the requested executable and package names."""
    return {
        "executables": {name: which(name) is not None for name in executable_names},
        "packages": {name: find_spec(name) is not None for name in package_names},
        "configured_runtime": configured_runtime(),
    }


def main():
    print(json.dumps(probe(EXECUTABLES, PACKAGES), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
