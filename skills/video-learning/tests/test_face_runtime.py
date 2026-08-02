import importlib.util
import unittest
from pathlib import Path


RUNTIME_SCRIPT = Path(__file__).parents[1] / "scripts" / "face_runtime.py"


class FaceRuntimeTest(unittest.TestCase):
    def test_runtime_script_configures_cuda_dll_paths(self):
        spec = importlib.util.spec_from_file_location("face_runtime", RUNTIME_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertTrue(callable(module.configure_cuda_dll_paths))
        self.assertEqual(module.configure_cuda_dll_paths(), module.configure_cuda_dll_paths())

    def test_face_analysis_runtime_is_importable(self):
        self.assertIsNotNone(importlib.util.find_spec("insightface"))
        from insightface.app import FaceAnalysis

        self.assertTrue(callable(FaceAnalysis))


if __name__ == "__main__":
    unittest.main()
