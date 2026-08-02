import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "screen_insta360_folder.py"


class ScreenInsta360FolderTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("screen_insta360_folder", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_recursively_lists_only_insv_sources_in_stable_path_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "z.insv").touch()
            (root / "ignore.mp4").touch()
            nested = root / "nested"
            nested.mkdir()
            (nested / "a.INSV").touch()

            sources = self.module.list_insv_sources(root)

        self.assertEqual([path.name for path in sources], ["a.INSV", "z.insv"])

    def test_builds_verified_full_export_command_with_per_source_output(self):
        command = self.module.build_full_export_command(
            "D:/work/MediaSDKDemo.exe",
            "D:/tools/MediaSDK",
            "F:/Insta360/test/327_002.insv",
            "D:/work/stitched/001-327_002_360.mp4",
        )

        self.assertEqual(
            command,
            [
                "D:/work/MediaSDKDemo.exe",
                "-inputs", "F:/Insta360/test/327_002.insv",
                "-output", "D:/work/stitched/001-327_002_360.mp4",
                "-model_root_dir", str(Path("D:/tools/MediaSDK") / "models"),
                "-stitch_type", "aistitch",
                "-bitrate", "60000000",
                "-enable_flowstate", "ON",
                "-output_size", "3840x1920",
                "-enable_h265_encoder", "h265",
                "-disable_cuda", "false",
            ],
        )

    def test_stitches_each_source_separately_then_passes_only_stitched_outputs_downstream(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "source"
            source_dir.mkdir()
            first = source_dir / "327_002.insv"
            second = source_dir / "327_004.insv"
            first.touch()
            second.touch()
            output_root = root / "delivery"
            stitched_calls = []
            downstream_sources = []

            def fake_stitch(source, output, **_):
                stitched_calls.append((source, output))
                output.write_bytes(b"stitched")

            def fake_batch(sources, output_root, **_):
                downstream_sources.extend(sources)
                return {"jobs": [{"source": str(source), "status": "partial"} for source in sources]}

            def raw_insv_inspection(source, **_):
                return {"path": str(source), "classification": {"kind": "raw_or_unknown_insv"}}

            manifest = self.module.run_folder(
                source_dir,
                output_root,
                sdk_root="D:/tools/MediaSDK",
                demo_exe="D:/work/MediaSDKDemo.exe",
                reference_dir="D:/refs",
                model_root="D:/models",
                threshold=0.60,
                stitcher=fake_stitch,
                batch_runner=fake_batch,
                inspect_fn=raw_insv_inspection,
            )

            written = json.loads((output_root / "insta360-folder-manifest.json").read_text(encoding="utf-8"))

        self.assertEqual([call[0].name for call in stitched_calls], ["327_002.insv", "327_004.insv"])
        self.assertEqual([path.name for path in downstream_sources], ["001-327_002_360.mp4", "002-327_004_360.mp4"])
        self.assertEqual([item["sdk_status"] for item in manifest["sources"]], ["complete", "complete"])
        self.assertEqual(written, manifest)

    def test_resume_reuses_an_existing_stitched_master_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "source"
            source_dir.mkdir()
            source = source_dir / "327_002.insv"
            source.touch()
            output_root = root / "delivery"
            stitched_dir = output_root / "stitched"
            stitched_dir.mkdir(parents=True)
            existing = stitched_dir / "001-327_002_360.mp4"
            existing.write_bytes(b"existing-master")
            stitched_calls = []

            def fake_stitch(*args, **kwargs):
                stitched_calls.append((args, kwargs))

            def fake_batch(sources, output_root, **_):
                return {"jobs": [{"source": str(item), "status": "partial"} for item in sources]}

            manifest = self.module.run_folder(
                source_dir,
                output_root,
                sdk_root="D:/tools/MediaSDK",
                demo_exe="D:/work/MediaSDKDemo.exe",
                reference_dir="D:/refs",
                model_root="D:/models",
                threshold=0.60,
                stitcher=fake_stitch,
                batch_runner=fake_batch,
                inspect_fn=lambda source, **_: {"path": str(source), "classification": {"kind": "raw_or_unknown_insv"}},
                resume=True,
            )

        self.assertEqual(stitched_calls, [])
        self.assertEqual(manifest["sources"][0]["sdk_status"], "reused_existing_stitched_output")
        self.assertEqual(manifest["sources"][0]["stitched_output"], str(existing))


if __name__ == "__main__":
    unittest.main()
