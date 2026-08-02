import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).parents[1] / "scripts" / "external_subtitles.py"


class ExternalSubtitleTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("external_subtitles", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_renders_raw_transcript_segments_as_standard_srt(self):
        rendered = self.module.render_srt(
            [
                {"start": 1.25, "end": 3.5, "text": "第一句"},
                {"start": 4.0, "end": 5.125, "text": "第二句"},
            ]
        )

        self.assertEqual(
            rendered,
            "1\n00:00:01,250 --> 00:00:03,500\n第一句\n\n"
            "2\n00:00:04,000 --> 00:00:05,125\n第二句\n",
        )

    def test_crops_candidate_subtitles_and_rebases_timestamps_to_clip_start(self):
        segments = self.module.crop_segments(
            [
                {"start": 8.0, "end": 10.0, "text": "前一句"},
                {"start": 10.5, "end": 12.0, "text": "中间一句"},
                {"start": 13.0, "end": 14.0, "text": "后一句"},
            ],
            start=9.0,
            end=13.0,
        )

        self.assertEqual(
            segments,
            [
                {"start": 0.0, "end": 1.0, "text": "前一句"},
                {"start": 1.5, "end": 3.0, "text": "中间一句"},
            ],
        )

    def test_keeps_translation_when_cropping_a_candidate_subtitle(self):
        segments = self.module.crop_segments(
            [{"start": 8.0, "end": 10.0, "text": "Open the project.", "translation": "打开项目。"}],
            start=9.0,
            end=11.0,
        )

        self.assertEqual(segments[0]["translation"], "打开项目。")

    def test_renders_original_and_chinese_translation_as_two_lines(self):
        rendered = self.module.render_srt(
            [
                {
                    "start": 1.0,
                    "end": 2.0,
                    "text": "Use the export button.",
                    "translation": "使用导出按钮。",
                }
            ]
        )

        self.assertEqual(
            rendered,
            "1\n00:00:01,000 --> 00:00:02,000\n"
            "Use the export button.\n使用导出按钮。\n",
        )

    def test_translates_non_chinese_segments_with_numbered_result_validation(self):
        translated, delivery = self.module.translate_for_chinese_subtitles(
            {
                "language": "en",
                "transcript_segments": [
                    {"start": 0.0, "end": 1.0, "text": "Open the project."},
                    {"start": 1.0, "end": 2.0, "text": "Export the result."},
                ],
            },
            lambda prompt: "1\t打开项目。\n2\t导出结果。",
        )

        self.assertEqual([segment["translation"] for segment in translated], ["打开项目。", "导出结果。"])
        self.assertEqual(delivery["translation_status"], "complete")
        self.assertEqual(delivery["target_language"], "zh-CN")

    def test_translates_large_transcript_in_numbered_batches_without_dropping_segments(self):
        calls = []

        def translator(prompt):
            calls.append(prompt)
            line_count = sum(1 for line in prompt.splitlines() if "\t" in line and line.split("\t", 1)[0].isdigit())
            return "\n".join(f"{index}\t第{index}条译文。" for index in range(1, line_count + 1))

        translated, delivery = self.module.translate_for_chinese_subtitles(
            {
                "language": "en",
                "transcript_segments": [
                    {"start": float(index), "end": float(index + 1), "text": f"Line {index}."}
                    for index in range(5)
                ],
            },
            translator,
            batch_size=2,
        )

        self.assertEqual(len(calls), 3)
        self.assertEqual([segment["translation"] for segment in translated], ["第1条译文。", "第2条译文。", "第1条译文。", "第2条译文。", "第1条译文。"])
        self.assertEqual(delivery["translation_status"], "complete")
        self.assertEqual(delivery["translated_segments"], 5)

    def test_groups_fragmented_asr_into_complete_sentence_units(self):
        units = self.module.build_semantic_units(
            [
                {"start": 0.0, "end": 1.0, "text": "My favorite job was"},
                {"start": 1.0, "end": 2.0, "text": "working with children."},
                {"start": 2.1, "end": 3.0, "text": "It was rewarding."},
            ]
        )

        self.assertEqual(
            units,
            [
                {"start": 0.0, "end": 2.0, "text": "My favorite job was working with children."},
                {"start": 2.1, "end": 3.0, "text": "It was rewarding."},
            ],
        )

    def test_does_not_split_a_comma_clause_at_a_short_pause(self):
        units = self.module.build_semantic_units(
            [
                {"start": 0.0, "end": 1.0, "text": "When we exercise,"},
                {"start": 2.0, "end": 3.0, "text": "our bodies adapt."},
            ]
        )

        self.assertEqual(
            units,
            [{"start": 0.0, "end": 3.0, "text": "When we exercise, our bodies adapt."}],
        )

    def test_uses_platform_caption_whose_midpoint_matches_the_asr_segment(self):
        segments = [{"start": 4.38, "end": 8.54, "text": "My favorite job."}]
        captions = [
            {"start": 0.0, "end": 7.0, "text": "翻译人员: Maxime Sobrier"},
            {"start": 4.368, "end": 8.472, "text": "我最喜欢的工作是当夏令营辅导员。"},
        ]

        aligned = self.module.apply_platform_caption_translations(segments, captions)

        self.assertEqual(aligned[0]["translation"], "我最喜欢的工作是当夏令营辅导员。")

    def test_uses_substantially_overlapping_platform_caption_at_a_segment_boundary(self):
        segments = [{"start": 220.37, "end": 221.09, "text": "So what do we do?"}]
        captions = [{"start": 220.417, "end": 222.319, "text": "那么我们该怎么做？"}]

        aligned = self.module.apply_platform_caption_translations(segments, captions)

        self.assertEqual(aligned[0]["translation"], "那么我们该怎么做？")

    def test_keeps_original_when_numbered_translation_is_incomplete(self):
        translated, delivery = self.module.translate_for_chinese_subtitles(
            {
                "language": "en",
                "transcript_segments": [
                    {"start": 0.0, "end": 1.0, "text": "Open the project."},
                    {"start": 1.0, "end": 2.0, "text": "Export the result."},
                ],
            },
            lambda prompt: "1\t打开项目。",
        )

        self.assertEqual(translated[0]["translation"], "打开项目。")
        self.assertNotIn("translation", translated[1])
        self.assertEqual(delivery["translation_status"], "partial")

    def test_retries_only_missing_translations_in_smaller_batches(self):
        calls = []

        def translator(prompt):
            source_lines = [line for line in prompt.splitlines() if "\t" in line and line.split("\t", 1)[0].isdigit()]
            calls.append(len(source_lines))
            if len(source_lines) > 1:
                return "1\t首条译文。"
            return "1\t补回译文。"

        translated, delivery = self.module.translate_for_chinese_subtitles(
            {
                "language": "en",
                "transcript_segments": [
                    {"start": 0.0, "end": 1.0, "text": "Line one."},
                    {"start": 1.0, "end": 2.0, "text": "Line two."},
                ],
            },
            translator,
            batch_size=2,
            retry_batch_size=1,
        )

        self.assertEqual(calls, [2, 1])
        self.assertEqual([segment["translation"] for segment in translated], ["首条译文。", "补回译文。"])
        self.assertEqual(delivery["translation_status"], "complete")

    def test_retries_a_suspect_final_translation_with_a_higher_local_output_limit(self):
        calls = []
        outputs = iter([
            "1\t第一句译文。\n2\t第二句半截",
            "1\t第二句完整译文。\n__TRANSLATION_COMPLETE__\n",
        ])

        def fake_run(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0, stdout=next(outputs), stderr="")

        translator = self.module.make_local_llama_translator(
            "D:/vision/runtime/llama-cli.exe",
            "D:/vision/models/Qwen.gguf",
            run=fake_run,
        )
        translated, delivery = self.module.translate_for_chinese_subtitles(
            {
                "language": "en",
                "transcript_segments": [
                    {"start": 0.0, "end": 1.0, "text": "First sentence."},
                    {"start": 1.0, "end": 2.0, "text": "Second sentence."},
                ],
            },
            translator,
            batch_size=2,
        )

        self.assertEqual([segment["translation"] for segment in translated], ["第一句译文。", "第二句完整译文。"])
        self.assertEqual(delivery["translation_status"], "complete")
        self.assertEqual([args[args.index("-n") + 1] for args in calls], ["512", "1024"])

    def test_rejects_foreign_source_text_echoed_as_a_translation(self):
        translated, delivery = self.module.translate_for_chinese_subtitles(
            {
                "language": "en",
                "transcript_segments": [
                    {"start": 0.0, "end": 1.0, "text": "Open the project."},
                    {"start": 1.0, "end": 2.0, "text": "Export the result."},
                ],
            },
            lambda prompt: "1\t打开项目。\n2\tExport the result.",
        )

        self.assertEqual(translated[0]["translation"], "打开项目。")
        self.assertNotIn("translation", translated[1])
        self.assertEqual(delivery["translation_status"], "partial")

    def test_prefers_generated_translation_after_prompt_echo(self):
        translations = self.module.parse_numbered_translations(
            "1\tOpen the project.\n1\t打开项目。\n",
            expected_count=1,
        )

        self.assertEqual(translations, {1: "打开项目。"})

    def test_accepts_chinese_translation_when_model_omits_the_tab_after_number(self):
        translations = self.module.parse_numbered_translations(
            "1\tOpen the project.\n2\tExport the final result.\n"
            "1\t打开项目。\n2导出最终结果。\n",
            expected_count=2,
        )

        self.assertEqual(translations, {1: "打开项目。", 2: "导出最终结果。"})

    def test_skips_translation_for_chinese_transcript(self):
        translated, delivery = self.module.translate_for_chinese_subtitles(
            {
                "language": "zh",
                "transcript_segments": [{"start": 0.0, "end": 1.0, "text": "原始中文"}],
            },
            lambda prompt: self.fail("Chinese transcript must not invoke translator"),
        )

        self.assertNotIn("translation", translated[0])
        self.assertEqual(delivery["translation_status"], "not_required")

    def test_local_llama_translator_uses_one_prompt_file_for_the_whole_batch(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout="1\t打开项目。\n", stderr="")

        translator = self.module.make_local_llama_translator(
            "D:/vision/runtime/llama-cli.exe",
            "D:/vision/models/Qwen.gguf",
            run=fake_run,
        )

        self.assertEqual(translator("1\tOpen the project."), "1\t打开项目。\n")
        self.assertEqual(calls[0][0][:3], ["D:/vision/runtime/llama-cli.exe", "-m", "D:/vision/models/Qwen.gguf"])
        self.assertIn("-f", calls[0][0])
        self.assertIn("--conversation", calls[0][0])
        self.assertIn("--single-turn", calls[0][0])
        self.assertNotIn("--mmproj", calls[0][0])


if __name__ == "__main__":
    unittest.main()
