import tempfile
import unittest
from pathlib import Path

from scripts.list_media import collect_media_paths, write_manifest


class CollectMediaPathsTests(unittest.TestCase):
    def test_writes_unicode_manifest_as_utf8(self):
        class Output:
            def __init__(self):
                self.encoding = None
                self.text = ""

            def reconfigure(self, *, encoding):
                self.encoding = encoding

            def write(self, text):
                self.text += text

        output = Output()
        write_manifest({"media": ["소원.mp4"]}, output)

        self.assertEqual(output.encoding, "utf-8")
        self.assertIn("소원.mp4", output.text)

    def test_collects_recursive_video_files_and_deduplicates_explicit_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "01-intro.mp4"
            second = root / "nested" / "02-demo.MKV"
            insta360 = root / "nested" / "03-360.insv"
            ignored = root / "notes.txt"
            second.parent.mkdir()
            first.touch()
            second.touch()
            insta360.touch()
            ignored.touch()

            result = collect_media_paths([root, first])

            self.assertEqual(result["media"], [str(first), str(second), str(insta360)])
            self.assertEqual(result["missing"], [])

    def test_reports_missing_inputs_without_discarding_valid_media(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            video = root / "lesson.mov"
            missing = root / "missing.mp4"
            video.touch()

            result = collect_media_paths([missing, video])

            self.assertEqual(result["media"], [str(video)])
            self.assertEqual(result["missing"], [str(missing)])


if __name__ == "__main__":
    unittest.main()
