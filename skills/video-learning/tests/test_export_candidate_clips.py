import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "export_candidate_clips.py"


class ExportCandidateClipsTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("export_candidate_clips", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_pads_candidate_without_exceeding_source_duration(self):
        start, end = self.module.clip_bounds({"start": 1.0, "end": 8.0}, duration=10.0, padding=2.0)

        self.assertEqual((start, end), (0.0, 10.0))

    def test_builds_precise_nvenc_clip_with_audio_preserved(self):
        command = self.module.build_clip_command(
            "D:/source.mp4", 10.0, 15.0, "D:/out.mp4", ffmpeg="ffmpeg"
        )

        self.assertIn("hevc_nvenc", command)
        self.assertIn("-c:a", command)
        self.assertIn("copy", command)
        self.assertIn("-t", command)

    def test_accepts_ranked_screening_candidate_manifests(self):
        intervals = self.module.candidate_intervals(
            {"candidates": [{"rank": 1, "start": 1.0, "end": 3.0}]}
        )

        self.assertEqual(intervals, [{"rank": 1, "start": 1.0, "end": 3.0}])

    def test_does_not_label_flat_video_clips_as_equirectangular(self):
        command = self.module.build_clip_command(
            "D:/source.mp4", 10.0, 15.0, "D:/out.mp4", ffmpeg="ffmpeg", equirectangular=False
        )

        self.assertNotIn("projection=equirectangular", command)
