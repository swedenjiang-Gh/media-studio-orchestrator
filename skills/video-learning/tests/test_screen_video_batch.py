import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "screen_video_batch.py"


class ScreenVideoBatchTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("screen_video_batch", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_creates_isolated_stable_output_directories_per_source(self):
        jobs = self.module.build_batch_jobs(
            ["D:/clips/one.mp4", "D:/clips/two.mp4"], "D:/work/screening"
        )

        self.assertEqual(jobs[0]["output_dir"], "D:/work/screening/001-one")
        self.assertEqual(jobs[1]["output_dir"], "D:/work/screening/002-two")
        self.assertEqual({job["status"] for job in jobs}, {"queued"})

    def test_detects_a_2_to_1_stitched_360_video(self):
        self.assertTrue(self.module.is_stitched_360({"streams": [{"codec_type": "video", "width": 3840, "height": 1920}]}))
        self.assertFalse(self.module.is_stitched_360({"streams": [{"codec_type": "video", "width": 1920, "height": 1080}]}))

    def test_blocks_speaker_attribution_without_independent_evidence(self):
        self.assertEqual(
            self.module.speaker_attribution_status(None),
            "blocked_missing_independent_voice_or_mouth_evidence",
        )

    def test_reports_unapproved_raw_transcript_as_review_only(self):
        self.assertEqual(
            self.module.dialogue_status({"quality_gate": "needs_manual_or_cross_modal_review"}),
            "review_only_needs_manual_or_cross_modal_review",
        )

    def test_writes_source_and_rebased_candidate_sidecar_subtitles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            master = output / "master.mp4"
            reframed = output / "reframed.mp4"
            delivery = self.module.write_subtitle_delivery(
                {"quality_gate": "needs_manual_or_cross_modal_review", "transcript_segments": [
                    {"start": 9.0, "end": 11.0, "text": "第一句"},
                    {"start": 12.0, "end": 13.0, "text": "第二句"},
                ]},
                output,
                [{"rank": 1, "start": 10.0, "end": 13.0}],
                [{"source_interval": {"start": 10.0, "end": 13.0}, "path": str(master)}],
                [{"rank": 1, "path": str(reframed)}],
            )

            master_srt = master.with_suffix(".srt").read_text(encoding="utf-8")
            reframed_srt = reframed.with_suffix(".srt").read_text(encoding="utf-8")

        self.assertEqual(delivery["quality_gate"], "needs_manual_or_cross_modal_review")
        self.assertEqual(delivery["masters"][0]["rank"], 1)
        self.assertIn("00:00:00,000 --> 00:00:01,000", master_srt)
        self.assertIn("00:00:00,000 --> 00:00:01,000", reframed_srt)

    def test_keeps_original_subtitles_when_translation_runtime_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            delivery = self.module.write_subtitle_delivery(
                {"language": "en", "transcript_segments": [
                    {"start": 0.0, "end": 1.0, "text": "Open the project."},
                ]},
                output,
                [],
                [],
                [],
                translator=lambda prompt: (_ for _ in ()).throw(RuntimeError("runtime failed")),
            )
            source_srt = (output / "source.srt").read_text(encoding="utf-8")

        self.assertEqual(delivery["translation"]["translation_status"], "blocked_local_translator_failed")
        self.assertEqual(source_srt, "1\n00:00:00,000 --> 00:00:01,000\nOpen the project.\n")

    def test_prefers_platform_captions_and_writes_complete_sentence_units(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            delivery = self.module.write_subtitle_delivery(
                {"language": "en", "transcript_segments": [
                    {"start": 0.0, "end": 1.0, "text": "Open the"},
                    {"start": 1.0, "end": 2.0, "text": "project."},
                ]},
                output,
                [],
                [],
                [],
                platform_captions=[{"start": 0.0, "end": 2.0, "text": "打开项目。"}],
            )
            source_srt = (output / "source.srt").read_text(encoding="utf-8")

        self.assertEqual(delivery["translation"]["translation_status"], "complete_platform_caption_aligned")
        self.assertEqual(source_srt, "1\n00:00:00,000 --> 00:00:02,000\nOpen the project.\n打开项目。\n")
