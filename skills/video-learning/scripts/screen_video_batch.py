"""Run verified local screening routes for a batch of flat or stitched-360 videos."""

import argparse
import json
import os
import re
from pathlib import Path


def safe_slug(path):
    """Return a stable output-directory fragment from a source filename."""
    return re.sub(r"[^0-9A-Za-z._-]+", "-", Path(path).stem).strip(".-") or "media"


def build_batch_jobs(sources, output_root):
    """Create queued jobs with isolated output directories without touching media files."""
    output_root = Path(output_root)
    return [
        {
            "source": str(source),
            "output_dir": str(output_root / f"{index:03d}-{safe_slug(source)}").replace("\\", "/"),
            "status": "queued",
        }
        for index, source in enumerate(sources, start=1)
    ]


def is_stitched_360(probe):
    """Recognize a practical 2:1 equirectangular MP4 route from stream dimensions."""
    for stream in probe.get("streams", []):
        if stream.get("codec_type") != "video":
            continue
        width, height = stream.get("width", 0), stream.get("height", 0)
        if height and abs(width / height - 2.0) <= 0.02:
            return True
    return False


def speaker_attribution_status(evidence):
    """Refuse speaker claims until an independent voice or mouth-motion source exists."""
    if not evidence:
        return "blocked_missing_independent_voice_or_mouth_evidence"
    return "pending_independent_evidence_review"


def dialogue_status(dialogue):
    """Expose raw transcript quality without promoting it to a dialogue claim."""
    if not dialogue:
        return "not_requested"
    gate = dialogue.get("quality_gate", "needs_manual_or_cross_modal_review")
    return "accepted" if gate == "passed" else f"review_only_{gate}"


def write_json(path, value):
    path = Path(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_subtitle_delivery(dialogue, output_dir, candidates, masters, reframed, translator=None, platform_captions=None):
    """Write source and derived-clip sidecar subtitles from preserved raw ASR segments."""
    from external_subtitles import (
        crop_segments,
        apply_platform_caption_translations,
        build_semantic_units,
        is_chinese_language,
        transcript_segments,
        translate_for_chinese_subtitles,
        write_srt,
    )

    output_dir = Path(output_dir)
    if is_chinese_language(dialogue.get("language")):
        segments, translation = translate_for_chinese_subtitles(dialogue, translator)
    elif platform_captions:
        segments = build_semantic_units(transcript_segments(dialogue))
        apply_platform_caption_translations(segments, platform_captions)
        missing_indexes = [index for index, segment in enumerate(segments) if "translation" not in segment]
        if missing_indexes and translator:
            missing = [segments[index] for index in missing_indexes]
            translated, fallback = translate_for_chinese_subtitles(
                {"language": dialogue.get("language"), "transcript_segments": missing}, translator,
            )
            for index, segment in zip(missing_indexes, translated):
                if segment.get("translation"):
                    segments[index]["translation"] = segment["translation"]
        remaining = [index + 1 for index, segment in enumerate(segments) if "translation" not in segment]
        translation = {
            "source_language": dialogue.get("language"),
            "target_language": "zh-CN",
            "translation_status": "complete_platform_caption_aligned" if not remaining else "partial_platform_caption_uncovered",
            "platform_caption_units": len(segments) - len(remaining),
            "total_segments": len(segments),
            "missing_units": remaining,
        }
    elif translator:
        try:
            segments, translation = translate_for_chinese_subtitles(dialogue, translator)
        except RuntimeError as error:
            segments = transcript_segments(dialogue)
            translation = {
                "source_language": dialogue.get("language"),
                "target_language": "zh-CN",
                "translation_status": "blocked_local_translator_failed",
                "error": str(error),
            }
    else:
        segments = transcript_segments(dialogue)
        translation = {
            "source_language": dialogue.get("language"),
            "target_language": "zh-CN",
            "translation_status": "blocked_missing_local_translator",
        }

    source = write_srt(output_dir / "source.srt", segments)
    candidate_by_rank = {candidate["rank"]: candidate for candidate in candidates}
    delivery = {
        "quality_gate": dialogue.get("quality_gate", "needs_manual_or_cross_modal_review"),
        "translation": translation,
        "source": str(source),
        "masters": [],
        "reframed": [],
    }
    for index, master in enumerate(masters, start=1):
        interval = master["source_interval"]
        subtitle = write_srt(
            Path(master["path"]).with_suffix(".srt"),
            crop_segments(segments, interval["start"], interval["end"]),
        )
        delivery["masters"].append({"rank": master.get("rank", index), "path": str(subtitle)})
    for clip in reframed:
        candidate = candidate_by_rank[clip["rank"]]
        subtitle = write_srt(
            Path(clip["path"]).with_suffix(".srt"),
            crop_segments(segments, candidate["start"], candidate["end"]),
        )
        delivery["reframed"].append({"rank": clip["rank"], "path": str(subtitle)})
    return delivery


def default_translation_paths():
    """Return this workstation's configurable local translation runtime paths."""
    root = Path(os.environ.get("VIDEO_LEARNING_ROOT", r"D:\CodexVideoLearning"))
    return (
        root / "vision" / "runtime" / "llama-cli.exe",
        root / "translation" / "models" / "qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf",
    )


def process_job(
    job, reference_dir, model_root, threshold, dialogue_model=None, ffmpeg="ffmpeg", ffprobe="ffprobe",
    dialogue_language=None, translation_runner=None, translation_model=None,
):
    """Run one supported local source and return a status record without modifying its original."""
    from build_screening_candidates import build_candidates, extract_candidate_frames, render_report
    from dialogue_candidates import transcribe_dialogue
    from export_candidate_clips import export_candidates
    from inspect_media import ffprobe_json
    from render_reframed_candidates import render_candidates
    from scan_360_known_faces import scan_360_known_faces
    from scan_events import scan_video
    from scan_known_faces import scan_known_faces

    source = Path(job["source"])
    output_dir = Path(job["output_dir"])
    if output_dir.exists():
        raise FileExistsError(f"Refusing to reuse an existing batch output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    probe = ffprobe_json(source, ffprobe)
    if source.suffix.lower() == ".insv" and not is_stitched_360(probe):
        return {**job, "status": "blocked", "reason": "raw_insv_requires_verified_sdk_or_stitched_export"}

    events = scan_video(source, ffmpeg=ffmpeg, ffprobe=ffprobe, scan_fps=2.0, hwaccel="cuda")
    stitched_360 = is_stitched_360(probe)
    if stitched_360:
        faces = scan_360_known_faces(source, reference_dir, model_root, threshold=threshold, ffmpeg=ffmpeg)
    else:
        faces = scan_known_faces(source, reference_dir, model_root, threshold=threshold, ffmpeg=ffmpeg, ffprobe=ffprobe)

    dialogue = None
    dialogue_path = None
    if dialogue_model:
        dialogue = transcribe_dialogue(source, dialogue_model, language=dialogue_language)
        dialogue_path = output_dir / "dialogue.json"
        write_json(dialogue_path, dialogue)
    candidates = build_candidates(events, faces, dialogue)
    extract_candidate_frames(source, candidates, output_dir / "evidence") if stitched_360 and candidates else None
    candidates_path = output_dir / "candidates.json"
    report_path = output_dir / "screening-report.md"
    write_json(candidates_path, {"candidates": candidates})
    report_path.write_text(render_report(candidates), encoding="utf-8")
    masters = export_candidates(
        source, candidates_path, output_dir / "master-candidates", ffmpeg=ffmpeg, ffprobe=ffprobe,
        equirectangular=stitched_360,
    )
    reframed = render_candidates(source, candidates_path, output_dir / "reframed-candidates", ffmpeg=ffmpeg) if stitched_360 and candidates else []
    delivery = {"masters": masters, "reframed": reframed}
    if dialogue:
        from external_subtitles import make_local_llama_translator, parse_webvtt_captions

        default_runner, default_model = default_translation_paths()
        translation_runner = Path(translation_runner or default_runner)
        translation_model = Path(translation_model or default_model)
        translator = None
        if not str(dialogue.get("language") or "").lower().startswith(("zh", "cmn", "yue")):
            if translation_runner.is_file() and translation_model.is_file():
                translator = make_local_llama_translator(translation_runner, translation_model)
        caption_path = source.with_suffix(".zh-CN.vtt")
        platform_captions = (
            parse_webvtt_captions(caption_path.read_text(encoding="utf-8"))
            if caption_path.is_file() else None
        )
        delivery["subtitles"] = write_subtitle_delivery(
            dialogue, output_dir, candidates, masters, reframed, translator=translator,
            platform_captions=platform_captions,
        )
    write_json(output_dir / "delivery.json", delivery)
    speaker_status = speaker_attribution_status(None)
    status = "complete" if speaker_status == "confirmed" else "partial"
    return {
        **job,
        "status": status,
        "stitched_360": stitched_360,
        "candidate_count": len(candidates),
        "dialogue": dialogue_status(dialogue),
        "speaker_attribution": speaker_status,
        "outputs": {
            "candidates": str(candidates_path),
            "report": str(report_path),
            "delivery": str(output_dir / "delivery.json"),
            **({"dialogue": str(dialogue_path)} if dialogue_path else {}),
        },
    }


def run_batch(
    sources, output_root, reference_dir, model_root, threshold, dialogue_model=None, ffmpeg="ffmpeg", ffprobe="ffprobe",
    dialogue_language=None, translation_runner=None, translation_model=None,
):
    """Process each source in order and preserve a combined batch status manifest."""
    output_root = Path(output_root)
    if output_root.exists():
        raise FileExistsError(f"Refusing to reuse an existing batch output root: {output_root}")
    output_root.mkdir(parents=True)
    jobs = build_batch_jobs(sources, output_root)
    results = []
    for job in jobs:
        try:
            results.append(process_job(
                job, reference_dir, model_root, threshold, dialogue_model, ffmpeg, ffprobe,
                dialogue_language, translation_runner, translation_model,
            ))
        except Exception as error:
            results.append({**job, "status": "blocked", "reason": str(error)})
    manifest = {"jobs": results}
    write_json(output_root / "batch-manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--reference-dir", required=True, type=Path)
    parser.add_argument("--model-root", required=True, type=Path)
    parser.add_argument("--threshold", required=True, type=float)
    parser.add_argument("--dialogue-model", type=Path)
    parser.add_argument("--dialogue-language", help="Optional ASR language override; omit to detect automatically.")
    parser.add_argument("--translation-runner", type=Path, help="Local llama.cpp-compatible executable for non-Chinese subtitles.")
    parser.add_argument("--translation-model", type=Path, help="Local GGUF model for non-Chinese subtitles.")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    print(json.dumps(
        run_batch(
            args.sources, args.output_root, args.reference_dir, args.model_root, args.threshold,
            args.dialogue_model, args.ffmpeg, args.ffprobe,
            args.dialogue_language, args.translation_runner, args.translation_model,
        ),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
