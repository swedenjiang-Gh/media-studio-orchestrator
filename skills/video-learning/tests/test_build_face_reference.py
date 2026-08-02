import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_face_reference.py"


class BuildFaceReferenceTest(unittest.TestCase):
    def test_selects_the_detected_face_that_overlaps_the_lightroom_label(self):
        spec = importlib.util.spec_from_file_location("build_face_reference", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        label = {
            "tl_x": "0.10", "tl_y": "0.10", "tr_x": "0.30", "tr_y": "0.10",
            "br_x": "0.30", "br_y": "0.30", "bl_x": "0.10", "bl_y": "0.30",
        }
        face = module.select_labeled_face(
            label,
            width=1000,
            height=1000,
            detections=[
                {"bbox": [700, 700, 850, 850], "det_score": 0.99},
                {"bbox": [105, 105, 295, 295], "det_score": 0.80},
            ],
        )

        self.assertEqual(face["bbox"], [105, 105, 295, 295])

    def test_reads_only_rows_that_have_a_local_photo_path(self):
        spec = importlib.util.spec_from_file_location("build_face_reference", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp:
            csv_path = Path(temp) / "people-faces.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["person", "photo_path"])
                writer.writeheader()
                writer.writerows([
                    {"person": "可用", "photo_path": "D:/photos/a.jpg"},
                    {"person": "缺失", "photo_path": ""},
                ])

            rows = module.read_face_rows(csv_path)

        self.assertEqual(rows, [{"person": "可用", "photo_path": "D:/photos/a.jpg"}])

    def test_reads_a_photo_from_a_unicode_path(self):
        spec = importlib.util.spec_from_file_location("build_face_reference", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory(prefix="人物-") as temp:
            target = Path(temp) / "姜小亮.jpg"
            encoded = cv2.imencode(".jpg", np.full((8, 9, 3), 127, dtype=np.uint8))[1]
            target.write_bytes(encoded.tobytes())

            image = module.read_image(target)

        self.assertEqual(image.shape, (8, 9, 3))

    def test_skips_a_lightroom_path_that_is_no_longer_available(self):
        spec = importlib.util.spec_from_file_location("build_face_reference", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        image = module.read_image(Path("D:/missing-photo.jpg"))

        self.assertIsNone(image)


if __name__ == "__main__":
    unittest.main()
