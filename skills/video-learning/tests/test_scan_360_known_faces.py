import importlib.util
import sys
import unittest
from unittest.mock import patch
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "scan_360_known_faces.py"


class Scan360KnownFacesTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("scan_360_known_faces", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_builds_cuda_projection_for_each_horizon_view(self):
        command = self.module.build_view_scan_command(
            "D:/clips/ride-360.mp4", "right", ffmpeg="ffmpeg", width=1280, sample_fps=2.0
        )

        self.assertEqual(command[:5], ["ffmpeg", "-hide_banner", "-nostdin", "-hwaccel", "cuda"])
        filters = command[command.index("-vf") + 1]
        self.assertIn("hwdownload,format=nv12", filters)
        self.assertIn("v360=input=equirect:output=flat:yaw=90:pitch=0", filters)
        self.assertIn("fps=2", filters)
        self.assertIn("w=1280:h=720", filters)

    def test_keeps_person_appearances_separate_by_view_direction(self):
        candidates = self.module.group_view_face_samples(
            [
                {"time": 1.0, "view": "front", "person": "姜小亮", "score": 0.73, "face_pixels": 100},
                {"time": 1.5, "view": "front", "person": "姜小亮", "score": 0.81, "face_pixels": 130},
                {"time": 1.5, "view": "back", "person": "姜小亮", "score": 0.78, "face_pixels": 120},
            ],
            max_gap_seconds=0.75,
            sample_interval_seconds=0.5,
        )

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["view"], "back")
        self.assertEqual(candidates[1]["view"], "front")
        self.assertEqual(candidates[1]["peak"], 1.5)

    def test_discards_ffmpeg_stderr_while_streaming_long_rawvideo_output(self):
        with patch.object(self.module.subprocess, "Popen", return_value="process") as popen:
            process = self.module.open_view_scan(["ffmpeg", "-version"])

        self.assertEqual(process, "process")
        self.assertIs(popen.call_args.kwargs["stderr"], self.module.subprocess.DEVNULL)
