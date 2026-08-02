import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "render_reframed_candidates.py"


class RenderReframedCandidatesTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("render_reframed_candidates", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_smooths_wrapped_yaw_without_large_direction_jumps(self):
        path = self.module.smooth_viewing_path(
            [
                {"time": 0.0, "yaw": 170, "pitch": 0},
                {"time": 1.0, "yaw": -175, "pitch": 2},
                {"time": 2.0, "yaw": -170, "pitch": 4},
            ]
        )

        self.assertLess(abs(path[1]["unwrapped_yaw"] - path[0]["unwrapped_yaw"]), 20)
        self.assertLess(abs(path[2]["unwrapped_yaw"] - path[1]["unwrapped_yaw"]), 20)

    def test_writes_relative_rotation_commands_for_a_candidate_interval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            command_file = Path(temp_dir) / "rotation.cmd"
            self.module.write_rotation_commands(
                command_file,
                [{"time": 10.0, "yaw": 90, "pitch": 0}, {"time": 12.0, "yaw": 100, "pitch": 5}],
                interval_start=10.0,
            )

            text = command_file.read_text(encoding="utf-8")
        self.assertIn("0.000 v360@viewer yaw 90", text)
        self.assertIn("2.000 v360@viewer pitch 5", text)

    def test_builds_1080p_20mbps_nvenc_reframe_with_audio(self):
        command = self.module.build_reframe_command(
            "D:/source.mp4", 10.0, 15.0, "D:/rotation.cmd", "D:/out.mp4", ffmpeg="ffmpeg"
        )

        self.assertIn("sendcmd", command[command.index("-filter_complex") + 1])
        self.assertIn("v360@viewer", command[command.index("-filter_complex") + 1])
        self.assertIn("hevc_nvenc", command)
        self.assertIn("20M", command)
        self.assertEqual(command[command.index("-c:a") + 1], "copy")
