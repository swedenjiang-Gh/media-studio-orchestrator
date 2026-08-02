import os
import unittest
from pathlib import Path

from scripts.insta360_sdk_frames import build_command, build_runtime_env, parse_output_size


class Insta360SdkFramesTests(unittest.TestCase):
    def test_builds_the_verified_official_demo_command(self):
        command = build_command(
            demo_exe="D:/work/MediaSDKDemo.exe",
            sdk_root="D:/tools/MediaSDK",
            inputs=["F:/Insta360/327_001.insv"],
            output_dir="D:/work/frames",
            frame_numbers=[0, 26970, 53900],
            output_size="3840x1920",
            stitch_type="optflow",
        )

        self.assertEqual(
            command,
            [
                "D:/work/MediaSDKDemo.exe",
                "-inputs",
                "F:/Insta360/327_001.insv",
                "-image_sequence_dir",
                "D:/work/frames",
                "-export_frame_index",
                "0-26970-53900",
                "-model_root_dir",
                str(Path("D:/tools/MediaSDK") / "models"),
                "-output_size",
                "3840x1920",
                "-stitch_type",
                "optflow",
            ],
        )

    def test_rejects_non_equirectangular_output_size(self):
        self.assertEqual(parse_output_size("3840x1920"), (3840, 1920))
        with self.assertRaisesRegex(ValueError, "2:1"):
            parse_output_size("3840x2160")

    def test_runtime_path_is_scoped_to_the_sdk_child_process(self):
        environment = build_runtime_env("D:/tools/MediaSDK", {"PATH": "base"})

        self.assertEqual(environment["PATH"], str(Path("D:/tools/MediaSDK") / "bin") + os.pathsep + "base")


if __name__ == "__main__":
    unittest.main()
