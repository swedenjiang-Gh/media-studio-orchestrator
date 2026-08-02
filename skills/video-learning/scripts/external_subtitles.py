"""Render raw timestamped transcript segments as external SRT subtitles."""

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


TRANSLATION_COMPLETE_MARKER = "__TRANSLATION_COMPLETE__"


def format_srt_time(seconds):
    """Format a non-negative timestamp as SRT timecode."""
    milliseconds = round(max(0.0, float(seconds)) * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def render_srt(segments):
    """Render timestamped raw ASR segments without rewriting their text."""
    blocks = []
    for index, segment in enumerate(segments, start=1):
        text = segment.get("text", "").strip()
        translation = segment.get("translation", "").strip()
        if not text or float(segment["end"]) <= float(segment["start"]):
            continue
        lines = [text]
        if translation:
            lines.append(translation)
        blocks.append(
            f"{index}\n{format_srt_time(segment['start'])} --> {format_srt_time(segment['end'])}\n"
            + "\n".join(lines)
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def crop_segments(segments, start, end):
    """Keep overlapping source segments and rebase them to a derived clip's start."""
    start, end = float(start), float(end)
    result = []
    for segment in segments:
        segment_start, segment_end = float(segment["start"]), float(segment["end"])
        overlap_start, overlap_end = max(start, segment_start), min(end, segment_end)
        if overlap_end <= overlap_start:
            continue
        cropped = {
            "start": round(overlap_start - start, 3),
            "end": round(overlap_end - start, 3),
            "text": segment.get("text", "").strip(),
        }
        if segment.get("translation", "").strip():
            cropped["translation"] = segment["translation"].strip()
        result.append(cropped)
    return result


def transcript_segments(dialogue):
    """Read the preserved raw ASR timecodes from a dialogue result."""
    return dialogue.get("transcript_segments", [])


def is_chinese_language(language):
    """Return whether ASR identified Chinese, including common locale tags."""
    return str(language or "").lower().startswith(("zh", "cmn", "yue"))


def translation_prompt(segments):
    """Build a constrained numbered translation request for one subtitle batch."""
    lines = [
        "Translate every numbered subtitle below into natural Simplified Chinese.",
        "Return exactly one line per input as: number<TAB>translation.",
        "Do not add notes, headings, markdown, timestamps, or omit any number.",
        "Preserve product names, commands, code, filenames, and numbers unless Chinese translation is standard.",
        f"After the final numbered line, add exactly: {TRANSLATION_COMPLETE_MARKER}",
        "",
    ]
    lines.extend(f"{index}\t{segment.get('text', '').strip()}" for index, segment in enumerate(segments, start=1))
    return "\n".join(lines)


def parse_numbered_translations(output, expected_count):
    """Accept only one non-empty tab-separated translation per expected segment."""
    translations = {}
    for line in output.splitlines():
        match = re.match(r"^\s*(\d+)(?:\t|(?=[\u4e00-\u9fff]))(.+?)\s*$", line)
        if not match:
            continue
        index, translation = int(match.group(1)), match.group(2).strip()
        if not translation:
            continue
        if 1 <= index <= expected_count:
            translations[index] = translation
    return translations


def normalized_subtitle_text(text):
    """Compare subtitle wording without case, whitespace, or punctuation noise."""
    return re.sub(r"[\W_]+", "", str(text).casefold())


def build_semantic_units(segments):
    """Merge adjacent ASR fragments until complete sentence punctuation."""
    units = []
    current = None
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
        start, end = float(segment["start"]), float(segment["end"])
        if current is None:
            current = {"start": start, "end": end, "text": text}
        else:
            current["end"] = end
            current["text"] = f"{current['text']} {text}"
        if re.search(r"[.!?。！？][\"')\]】》]*$", text):
            units.append(current)
            current = None
    if current:
        units.append(current)
    return units


def parse_webvtt_time(value):
    """Parse a WebVTT timestamp into seconds."""
    parts = value.strip().replace(",", ".").split(":")
    if len(parts) == 2:
        hours, minutes, seconds = 0, *parts
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Invalid WebVTT timestamp: {value}")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_webvtt_captions(text):
    """Read timed WebVTT captions while preserving each caption's visible lines."""
    captions = []
    for block in re.split(r"\r?\n\s*\r?\n", text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start, end = lines[timing_index].split("-->", 1)
        caption_text = " ".join(lines[timing_index + 1:]).strip()
        if caption_text:
            captions.append({
                "start": parse_webvtt_time(start),
                "end": parse_webvtt_time(end.split()[0]),
                "text": caption_text,
            })
    return captions


def apply_platform_caption_translations(segments, captions):
    """Use platform subtitle lines whose midpoint falls inside each ASR segment."""
    for segment in segments:
        start, end = float(segment["start"]), float(segment["end"])
        matched = [
            caption["text"].strip()
            for caption in captions
            if start <= (float(caption["start"]) + float(caption["end"])) / 2 <= end
        ]
        if not matched:
            overlaps = [
                (max(0.0, min(end, float(caption["end"])) - max(start, float(caption["start"]))), caption["text"].strip())
                for caption in captions
            ]
            overlap, text = max(overlaps, default=(0.0, ""))
            if overlap >= (end - start) * 0.2:
                matched = [text]
        if matched:
            segment["translation"] = " ".join(dict.fromkeys(matched))
    return segments


def translate_for_chinese_subtitles(dialogue, translator, batch_size=40, retry_batch_size=None):
    """Add validated Chinese translations without modifying raw ASR wording or timecodes."""
    segments = [dict(segment) for segment in transcript_segments(dialogue)]
    language = dialogue.get("language")
    delivery = {
        "source_language": language,
        "target_language": "zh-CN",
        "translation_status": "not_required" if is_chinese_language(language) else "pending",
    }
    if delivery["translation_status"] == "not_required":
        return segments, delivery

    def translate_batches(candidates, size, output_max_tokens=None):
        suspect_final_segments = []
        for batch_start in range(0, len(candidates), size):
            batch = candidates[batch_start:batch_start + size]
            prompt = translation_prompt(batch)
            if output_max_tokens is None:
                output = translator(prompt)
            else:
                output = translator(prompt, output_max_tokens=output_max_tokens)
            translations = parse_numbered_translations(output, len(batch))
            requires_completion_marker = bool(getattr(translator, "supports_output_limit", False))
            complete = (
                len(translations) == len(batch)
                and (not requires_completion_marker or output.rstrip().endswith(TRANSLATION_COMPLETE_MARKER))
            )
            for index, segment in enumerate(batch, start=1):
                if (
                    index in translations
                    and (complete or not requires_completion_marker or index != len(batch))
                    and normalized_subtitle_text(segment.get("text")) != normalized_subtitle_text(translations[index])
                ):
                    segment["translation"] = translations[index]
            if requires_completion_marker and not complete:
                suspect_final_segments.extend(
                    segment
                    for index, segment in enumerate(batch, start=1)
                    if index not in translations or index == len(batch)
                )
        return suspect_final_segments

    suspect_final_segments = translate_batches(segments, batch_size)
    if getattr(translator, "supports_output_limit", False):
        seen = set()
        for segment in suspect_final_segments:
            identity = id(segment)
            if identity in seen:
                continue
            seen.add(identity)
            translate_batches([segment], 1, output_max_tokens=1024)
    missing = [segment for segment in segments if "translation" not in segment]
    if missing and retry_batch_size:
        translate_batches(missing, retry_batch_size)
    translated_segments = sum("translation" in segment for segment in segments)
    delivery["translation_status"] = "complete" if translated_segments == len(segments) else "partial"
    delivery["translated_segments"] = translated_segments
    delivery["total_segments"] = len(segments)
    return segments, delivery


def make_local_llama_translator(runner, model, max_tokens=512, run=subprocess.run):
    """Return a batch translator backed by a local llama.cpp-compatible model."""
    runner, model = str(runner), str(model)

    def translate(prompt, output_max_tokens=None):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as handle:
            handle.write(prompt)
            prompt_path = Path(handle.name)
        try:
            command = [runner, "-m", model]
            command.extend([
                "-f", str(prompt_path), "-n", str(max_tokens if output_max_tokens is None else output_max_tokens), "--temp", "0", "--conversation",
                "--single-turn", "--no-display-prompt", "--no-warmup", "--simple-io",
            ])
            result = run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        finally:
            prompt_path.unlink(missing_ok=True)
        if result.returncode != 0:
            raise RuntimeError(f"Local subtitle translator failed: {result.stderr.strip()}")
        return result.stdout

    translate.supports_output_limit = True
    return translate


def write_srt(path, segments):
    """Write one new UTF-8 SRT file without replacing a prior delivery."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite external subtitle file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_srt(segments), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dialogue_json", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-start", type=float, default=0.0)
    parser.add_argument("--source-end", type=float)
    args = parser.parse_args()

    dialogue = json.loads(args.dialogue_json.read_text(encoding="utf-8"))
    segments = transcript_segments(dialogue)
    if args.source_end is not None:
        segments = crop_segments(segments, args.source_start, args.source_end)
    elif args.source_start:
        segments = crop_segments(segments, args.source_start, float("inf"))
    output = write_srt(args.output, segments)
    print(json.dumps({"subtitle": str(output), "segments": len(segments)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
