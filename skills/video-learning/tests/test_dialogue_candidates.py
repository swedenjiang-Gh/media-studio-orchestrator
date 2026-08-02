import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "dialogue_candidates.py"


class DialogueCandidateTest(unittest.TestCase):
    def test_groups_adjacent_transcript_segments_with_raw_text_preserved(self):
        spec = importlib.util.spec_from_file_location("dialogue_candidates", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        candidates = module.group_dialogue_segments(
            [
                {"start": 10.0, "end": 11.0, "text": "爸爸"},
                {"start": 11.3, "end": 13.0, "text": "我们去哪儿"},
                {"start": 20.0, "end": 21.0, "text": "好"},
            ],
            max_gap_seconds=0.5,
        )

        self.assertEqual(candidates[0], {"start": 10.0, "end": 13.0, "raw_text": "爸爸 我们去哪儿", "segment_count": 2})
        self.assertEqual(candidates[1]["start"], 20.0)

    def test_rejects_obviously_repeated_raw_asr_from_dialogue_claims(self):
        spec = importlib.util.spec_from_file_location("dialogue_candidates", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.assess_transcript_quality(
            [
                {"text": "好的 好的"},
                {"text": "好的 好的"},
                {"text": "好的 好的"},
            ]
        )

        self.assertEqual(result, "rejected")
