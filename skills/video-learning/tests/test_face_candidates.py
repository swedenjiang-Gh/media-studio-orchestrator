import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "face_candidates.py"


class FaceCandidateTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("face_candidates", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_scores_people_by_their_best_reference_embeddings(self):
        scores = self.module.score_people(
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([[1.0, 0.0], [0.98, 0.02], [0.0, 1.0]], dtype=np.float32),
            ["姜小亮", "姜小亮", "姜吴虞"],
            top_k=2,
        )

        self.assertGreater(scores["姜小亮"], 0.98)
        self.assertLess(scores["姜吴虞"], 0.01)

    def test_groups_continuous_face_samples_into_a_candidate_interval(self):
        intervals = self.module.group_face_samples(
            [
                {"time": 1.0, "person": "姜小亮", "score": 0.73, "face_pixels": 90},
                {"time": 2.0, "person": "姜小亮", "score": 0.80, "face_pixels": 130},
                {"time": 3.0, "person": "姜小亮", "score": 0.77, "face_pixels": 110},
                {"time": 8.0, "person": "姜小亮", "score": 0.92, "face_pixels": 160},
            ],
            max_gap_seconds=1.5,
            sample_interval_seconds=1.0,
        )

        self.assertEqual(len(intervals), 2)
        self.assertEqual(intervals[0]["person"], "姜小亮")
        self.assertEqual(intervals[0]["start"], 1.0)
        self.assertEqual(intervals[0]["end"], 4.0)
        self.assertEqual(intervals[0]["peak"], 2.0)
