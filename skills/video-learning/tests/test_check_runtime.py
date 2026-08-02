import os
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_runtime


class CheckRuntimeConfigurationTests(unittest.TestCase):
    def test_workspace_root_uses_video_learning_root_environment_variable(self):
        with patch.dict(os.environ, {"VIDEO_LEARNING_ROOT": r"E:\\VideoLearning"}):
            self.assertTrue(hasattr(check_runtime, "workspace_root"))
            self.assertEqual(check_runtime.workspace_root(), Path(r"E:\VideoLearning"))


if __name__ == "__main__":
    unittest.main()
