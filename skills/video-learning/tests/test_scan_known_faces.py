import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "scan_known_faces.py"


class ScanKnownFacesTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("scan_known_faces", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_gpu_scan_command_samples_and_downscales_before_face_inference(self):
        command = self.module.build_scan_command(
            "D:/clips/ride.mp4", ffmpeg="ffmpeg", width=1280, sample_fps=2.0
        )

        self.assertEqual(command[:5], ["ffmpeg", "-hide_banner", "-nostdin", "-hwaccel", "cuda"])
        filters = command[command.index("-vf") + 1]
        self.assertIn("fps=2", filters)
        self.assertIn("scale_cuda=1280:-2", filters)
        self.assertIn("bgr24", filters)

    def test_marks_identity_as_review_until_the_score_clears_the_threshold(self):
        self.assertEqual(
            self.module.identity_result({"姜小亮": 0.61, "姜吴虞": 0.42}, threshold=0.65),
            {"person": "姜小亮", "score": 0.61, "status": "unverified"},
        )
        self.assertEqual(
            self.module.identity_result({"姜小亮": 0.71}, threshold=0.65),
            {"person": "姜小亮", "score": 0.71, "status": "review_candidate"},
        )
