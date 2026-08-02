import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "calibrate_face_threshold.py"


class FaceThresholdCalibrationTest(unittest.TestCase):
    def test_review_threshold_stays_above_the_high_impostor_score(self):
        spec = importlib.util.spec_from_file_location("calibrate_face_threshold", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        threshold = module.choose_review_threshold([0.31, 0.44, 0.58], minimum=0.5, quantile=1.0)

        self.assertGreater(threshold, 0.58)
