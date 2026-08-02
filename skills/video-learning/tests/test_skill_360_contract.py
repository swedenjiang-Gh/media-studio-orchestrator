import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "SKILL.md"


class PanoramaScreeningContractTest(unittest.TestCase):
    def test_skill_requires_verified_sdk_route_and_two_derived_outputs(self):
        content = SKILL.read_text(encoding="utf-8")

        for required in (
            "Desktop Media SDK",
            "SDK route is verified",
            "360 master candidate",
            "reframed candidate",
            "speaker attribution",
            "selected-frame export is verified",
            "2:1 equirectangular",
            "selected-frame export",
            "community CLI",
        ):
            self.assertIn(required, content)

    def test_skill_records_the_verified_sdk_frame_route_and_interval_boundary(self):
        content = SKILL.read_text(encoding="utf-8")
        pending = (SKILL.parent / "references" / "v2-pending-design.md").read_text(encoding="utf-8")

        self.assertIn("scripts/insta360_sdk_frames.py", content)
        self.assertIn("selected-frame export is verified", content)
        self.assertIn("does not expose a bounded MP4 interval export", content)
        self.assertIn("327_001.insv", pending)
        self.assertIn("MediaSDK 3.1.3.1", pending)

    def test_skill_records_verified_full_export_and_review_only_face_dialogue_routes(self):
        content = SKILL.read_text(encoding="utf-8")

        self.assertIn("full-video export is verified", content)
        self.assertIn("scripts/build_face_reference.py", content)
        self.assertIn("scripts/scan_known_faces.py", content)
        self.assertIn("scripts/dialogue_candidates.py", content)
        self.assertIn("scripts/export_candidate_clips.py", content)
        self.assertIn("raw review candidates", content)

    def test_skill_documents_verified_batch_delivery_and_speaker_block(self):
        content = SKILL.read_text(encoding="utf-8")

        for required in (
            "scripts/scan_360_known_faces.py",
            "scripts/build_screening_candidates.py",
            "scripts/render_reframed_candidates.py",
            "scripts/screen_video_batch.py",
            "blocked_missing_independent_voice_or_mouth_evidence",
        ):
            self.assertIn(required, content)


if __name__ == "__main__":
    unittest.main()
