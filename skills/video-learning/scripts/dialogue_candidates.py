"""Create timestamped dialogue-review candidates with local Whisper VAD transcription."""

import argparse
import json
from pathlib import Path


def assess_transcript_quality(segments):
    """Reject only obvious ASR repetition; all other transcripts still require evidence review."""
    texts = [segment.get("text", "").strip() for segment in segments if segment.get("text", "").strip()]
    if not texts:
        return "rejected"
    repeated = max(texts.count(text) for text in set(texts))
    if len(texts) >= 3 and repeated / len(texts) >= 0.6:
        return "rejected"
    return "needs_manual_or_cross_modal_review"


def group_dialogue_segments(segments, max_gap_seconds=0.8):
    """Merge adjacent speech transcript segments without altering their recognized wording."""
    groups = []
    for segment in segments:
        if groups and segment["start"] - groups[-1]["end"] <= max_gap_seconds:
            groups[-1]["end"] = segment["end"]
            groups[-1]["texts"].append(segment["text"])
            groups[-1]["segment_count"] += 1
        else:
            groups.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "texts": [segment["text"]],
                    "segment_count": 1,
                }
            )
    return [
        {
            "start": group["start"],
            "end": group["end"],
            "raw_text": " ".join(group["texts"]),
            "segment_count": group["segment_count"],
        }
        for group in groups
    ]


def transcribe_dialogue(source, model_path, language=None):
    """Transcribe local media on CUDA with VAD while retaining raw segment text and timecodes."""
    from face_runtime import configure_cuda_dll_paths

    configure_cuda_dll_paths()
    from faster_whisper import WhisperModel

    model = WhisperModel(str(model_path), device="cuda", compute_type="float16")
    kwargs = {"beam_size": 5, "vad_filter": True, "condition_on_previous_text": False}
    if language:
        kwargs["language"] = language
    segments, info = model.transcribe(str(source), **kwargs)
    raw_segments = [
        {"start": round(float(segment.start), 3), "end": round(float(segment.end), 3), "text": segment.text.strip()}
        for segment in segments
        if segment.text.strip()
    ]
    return {
        "source": str(Path(source).resolve()),
        "language": info.language,
        "language_probability": round(float(info.language_probability), 6),
        "transcript_segments": raw_segments,
        "dialogue_candidates": group_dialogue_segments(raw_segments),
        "quality_gate": assess_transcript_quality(raw_segments),
        "speaker_attribution": "not_attempted_without_independent voice or mouth-motion evidence",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--language")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing dialogue candidates: {args.output}")
    result = transcribe_dialogue(args.source, args.model_path, args.language)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"segments": len(result["transcript_segments"]), "candidates": len(result["dialogue_candidates"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
