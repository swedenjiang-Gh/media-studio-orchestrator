import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VideoLearningSkillContractTests(unittest.TestCase):
    def test_skill_supports_mixed_batches_and_local_folder_discovery(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("multiple local video files", skill)
        self.assertIn("folders", skill)
        self.assertIn("scripts/list_media.py", skill)
        self.assertIn("final combined results", skill)

    def test_readme_describes_complete_local_video_as_the_default(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("完整本地视频", readme)
        self.assertIn("文件夹", readme)
        self.assertIn("视觉模型", readme)

    def test_skill_routes_raw_insta360_and_uses_event_intervals_not_fixed_sampling(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Insta360 Studio", skill)
        self.assertIn("event intervals", skill)
        self.assertIn("not a fixed-interval primary analysis", skill)

    def test_skill_requires_evidence_led_visual_notes_and_named_entity_cross_checks(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Evidence-led visual notes", skill)
        self.assertIn("small, decisive set of original keyframes", skill)
        self.assertIn("ASR or visual-model output alone", skill)
        self.assertIn("author-reported claim", skill)

    def test_skill_describes_v2_reliability_and_insta360_tools(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("scripts/check_capture.py", skill)
        self.assertIn("scripts/v2_state.py", skill)
        self.assertIn("scripts/inspect_media.py", skill)
        self.assertIn("scripts/scan_events.py", skill)
        self.assertIn("scripts/extract_event_frames.py", skill)
        self.assertIn("scripts/extract_360_views.py", skill)
        self.assertIn("overlapping rectilinear views", skill)
        self.assertIn("new capture segment", skill)
        self.assertIn("resume-point", skill)

    def test_skill_supports_video_understanding_screening_and_candidate_extraction(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("视频理解、筛片、粗剪与信息提取", skill)
        self.assertIn("精彩片段候选", skill)
        self.assertIn("互动/对话候选", skill)
        self.assertIn("user-provided context", skill)
        self.assertIn("候选片段导出", skill)

    def test_skill_requires_exact_lightroom_working_directory_and_index_reuse(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("user-specified Lightroom working directory", skill)
        self.assertIn("Do not search parent directories", skill)
        self.assertIn("reuse that index", skill)
        self.assertIn("references/local-machine.md", skill)


if __name__ == "__main__":
    unittest.main()
