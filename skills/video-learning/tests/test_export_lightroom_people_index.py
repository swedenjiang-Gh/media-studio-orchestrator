import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "export_lightroom_people_index.py"


class LightroomPeopleIndexTest(unittest.TestCase):
    def test_script_exposes_person_summary_and_photo_face_rows(self):
        spec = importlib.util.spec_from_file_location("lightroom_people_index", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertIn("people-summary.csv", module.OUTPUT_FILES)
        self.assertIn("people-photos.csv", module.OUTPUT_FILES)
        self.assertIn("people-faces.csv", module.OUTPUT_FILES)
        self.assertTrue(module.PEOPLE_SQL.lstrip().lower().startswith("with valid_faces"))
        self.assertIn("keywordType = 'person'", module.PEOPLE_SQL)
        self.assertIn("coalesce(kf.userReject, 0) = 0", module.PEOPLE_SQL)
        self.assertIn("coalesce(f.ignored, 0) = 0", module.PEOPLE_SQL)


if __name__ == "__main__":
    unittest.main()
