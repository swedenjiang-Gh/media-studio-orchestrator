import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_screening_candidates.py"


class BuildScreeningCandidatesTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("build_screening_candidates", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_merges_overlapping_event_and_face_evidence_into_one_candidate(self):
        candidates = self.module.build_candidates(
            {"intervals": [{"start": 4.0, "peak": 5.0, "end": 6.0, "peak_score": 8.0}]},
            {
                "review_candidates": [
                    {
                        "person": "姜小亮",
                        "view": "back",
                        "start": 4.5,
                        "peak": 5.5,
                        "end": 7.0,
                        "peak_score": 0.73,
                        "peak_face_pixels": 130,
                        "sample_count": 4,
                    }
                ]
            },
            None,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual((candidate["start"], candidate["end"]), (4.0, 7.0))
        self.assertEqual(candidate["preferred_view"], "back")
        self.assertEqual(candidate["face_review_candidates"][0]["person"], "姜小亮")
        self.assertIn("visual_change", candidate["evidence_labels"])
        self.assertIn("clear_face_review_candidate", candidate["evidence_labels"])

    def test_rejected_transcript_does_not_add_dialogue_claims(self):
        candidates = self.module.build_candidates(
            {"intervals": []},
            {"review_candidates": []},
            {
                "quality_gate": "rejected",
                "dialogue_candidates": [{"start": 1.0, "end": 4.0, "raw_text": "错误文字"}],
            },
        )

        self.assertEqual(candidates, [])

    def test_report_marks_names_as_review_candidates(self):
        report = self.module.render_report(
            [{"rank": 1, "start": 1.0, "end": 3.0, "peak": 2.0, "score": 4.2,
              "preferred_view": "back", "evidence_labels": ["clear_face_review_candidate"],
              "face_review_candidates": [{"person": "姜小亮", "peak_score": 0.73}],
              "dialogue_candidates": [], "evidence_frames": []}]
        )

        self.assertIn("候选 1", report)
        self.assertIn("复核候选", report)
        self.assertIn("00:00:01.000", report)

    def test_attaches_extracted_frames_to_their_candidate_order(self):
        candidates = [{"evidence_frames": []}, {"evidence_frames": []}]
        frames = [
            {"event_id": "event-002", "role": "peak"},
            {"event_id": "event-001", "role": "start"},
        ]

        result = self.module.attach_event_frames(candidates, frames)

        self.assertEqual(result[0]["evidence_frames"], [{"event_id": "event-001", "role": "start"}])
        self.assertEqual(result[1]["evidence_frames"], [{"event_id": "event-002", "role": "peak"}])

    def test_derives_face_centered_viewing_path_from_timed_360_face_samples(self):
        candidate = {"start": 4.0, "end": 6.0, "preferred_view": "front"}
        samples = [
            {"time": 4.5, "view": "front", "faces": [{"bbox": [900, 300, 1020, 420],
             "fully_inside_frame": True, "identity": {"status": "review_candidate"}}]},
            {"time": 5.5, "view": "front", "faces": [{"bbox": [820, 300, 940, 420],
             "fully_inside_frame": True, "identity": {"status": "review_candidate"}}]},
        ]

        path = self.module.derive_viewing_path(candidate, samples, scan_width=1280, scan_height=720)

        self.assertEqual([point["time"] for point in path], [4.0, 4.5, 5.5, 6.0])
        self.assertAlmostEqual(path[1]["yaw"], 25.0)
        self.assertAlmostEqual(path[1]["pitch"], 0.0)

    def test_accepts_flat_video_face_evidence_without_a_360_view_field(self):
        candidates = self.module.build_candidates(
            {"intervals": []},
            {"scan_width": 1280, "scan_height": 720,
             "samples": [{"time": 1.0, "faces": []}],
             "review_candidates": [{"person": "姜小亮", "start": 1.0, "end": 2.0, "peak": 1.0,
                                    "peak_score": 0.7, "peak_face_pixels": 100, "sample_count": 2}]},
            None,
        )

        self.assertEqual(candidates[0]["preferred_view"], "front")
