"""Initialize the local CUDA face-recognition runtime without changing system PATH."""

import os
import site
from pathlib import Path


_DLL_DIRECTORY_HANDLES = []
_CUDA_DLL_DIRECTORIES = []


def configure_cuda_dll_paths() -> list[str]:
    """Expose CUDA wheel DLLs to this Python process and retain their handles."""
    if _DLL_DIRECTORY_HANDLES:
        return _CUDA_DLL_DIRECTORIES
    package_root = next(
        path for path in map(Path, site.getsitepackages()) if (path / "nvidia").is_dir()
    )
    directories = sorted(
        (path for path in (package_root / "nvidia").glob("*/bin") if path.is_dir()),
        key=lambda path: str(path).casefold(),
    )
    _CUDA_DLL_DIRECTORIES.extend(str(path) for path in directories)
    os.environ["PATH"] = os.pathsep.join(_CUDA_DLL_DIRECTORIES + [os.environ["PATH"]])
    _DLL_DIRECTORY_HANDLES.extend(os.add_dll_directory(path) for path in _CUDA_DLL_DIRECTORIES)
    return _CUDA_DLL_DIRECTORIES


def create_face_analysis(model_root: str | Path, detection_size=(640, 640), threshold=0.55):
    """Create antelopev2 on CUDA and refuse a silent CPU fallback."""
    configure_cuda_dll_paths()
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(
        name="antelopev2",
        root=str(model_root),
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=detection_size, det_thresh=threshold)
    unexpected = {
        name: model.session.get_providers()
        for name, model in app.models.items()
        if model.session.get_providers()[0] != "CUDAExecutionProvider"
    }
    if unexpected:
        raise RuntimeError(f"CUDA face runtime unavailable: {unexpected}")
    return app
