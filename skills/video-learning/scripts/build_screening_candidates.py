"""Fuse visual-change, face, and quality-gated dialogue evidence into review candidates."""

import argparse
import json
from pathlib import Path


VIEW_YAWS = {"front": 0, "right": 90, "back": 180, "left": -90}


def format_time(seconds):
    """Format a source timestamp for a review report."""
    milliseconds = round((seconds - int(seconds)) * 1000)
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}.{milliseconds:03d}"


def quality_dialogues(dialogue_data):
    """Return dialogue evidence only after the caller has accepted the transcript quality gate."""
    if not dialogue_data or dialogue_data.get("quality_gate") != "passed":
        return []
    return dialogue_data.get("dialogue_candidates", [])


def merge_intervals(evidence, max_gap_seconds=1.0):
    """Group adjacent evidence while preserving the original evidence type and timestamp."""
    ordered = sorted(evidence, key=lambda item: (item["start"], item["end"]))
    groups = []
    for item in ordered:
        if groups and item["start"] <= groups[-1]["end"] + max_gap_seconds:
            groups[-1]["items"].append(item)
            groups[-1]["end"] = max(groups[-1]["end"], item["end"])
            groups[-1]["start"] = min(groups[-1]["start"], item["start"])
        else:
            groups.append({"start": item["start"], "end": item["end"], "items": [item]})
    return groups


def face_view(faces):
    """Choose the strongest visible direction for a review viewing path."""
    if not faces:
        return "front"
    best = max(faces, key=lambda face: (face["peak_face_pixels"], face["peak_score"], face["sample_count"]))
    return best.get("view", "front")


def candidate_score(events, faces, dialogues):
    """Return a transparent ranking score from independent, reviewable evidence."""
    activity = min(2.0, float(len(events)))
    face_visibility = min(4.0, sum(float(face["sample_count"]) * 0.2 for face in faces))
    speech = min(2.0, float(len(dialogues)))
    return round(activity + face_visibility + speech, 3), {
        "visual_change": activity,
        "clear_face_review_candidate": round(face_visibility, 3),
        "quality_gated_dialogue": speech,
    }


def derive_viewing_path(candidate, samples, scan_width, scan_height):
    """Aim a 360 viewing path at the strongest review-level face in the selected direction."""
    view = candidate["preferred_view"]
    observed = []
    for sample in samples:
        if not candidate["start"] <= sample["time"] <= candidate["end"] or sample.get("view", "front") != view:
            continue
        faces = [
            face for face in sample["faces"]
            if face["fully_inside_frame"] and face["identity"]["status"] == "review_candidate"
        ]
        if not faces:
            continue
        face = max(faces, key=lambda item: min(item["bbox"][2] - item["bbox"][0], item["bbox"][3] - item["bbox"][1]))
        x0, y0, x1, y1 = face["bbox"]
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        observed.append(
            {
                "time": sample["time"],
                "yaw": VIEW_YAWS[view] + (center_x / scan_width - 0.5) * 100,
                "pitch": (0.5 - center_y / scan_height) * 75,
            }
        )
    if not observed:
        observed = [{"time": candidate["start"], "yaw": VIEW_YAWS[view], "pitch": 0}]
    if observed[0]["time"] != candidate["start"]:
        observed.insert(0, {**observed[0], "time": candidate["start"]})
    if observed[-1]["time"] != candidate["end"]:
        observed.append({**observed[-1], "time": candidate["end"]})
    return observed


def build_candidates(event_data, face_data, dialogue_data):
    """Build ranked review candidates without promoting uncertain names or rejected ASR."""
    evidence = []
    for interval in event_data.get("intervals", []):
        evidence.append({"kind": "event", **interval})
    for interval in face_data.get("review_candidates", []):
        evidence.append({"kind": "face", **interval})
    for interval in quality_dialogues(dialogue_data):
        evidence.append({"kind": "dialogue", **interval})

    candidates = []
    for group in merge_intervals(evidence):
        events = [item for item in group["items"] if item["kind"] == "event"]
        faces = [item for item in group["items"] if item["kind"] == "face"]
        dialogues = [item for item in group["items"] if item["kind"] == "dialogue"]
        labels = []
        if events:
            labels.append("visual_change")
        if faces:
            labels.append("clear_face_review_candidate")
        if dialogues:
            labels.append("quality_gated_dialogue")
        preferred_view = face_view(faces)
        peak_items = events + faces + dialogues
        peak_item = max(peak_items, key=lambda item: (item.get("peak_score", 0), item.get("face_pixels", 0)))
        score, score_components = candidate_score(events, faces, dialogues)
        candidate = {
                "start": round(float(group["start"]), 3),
                "end": round(float(group["end"]), 3),
                "peak": round(float(peak_item.get("peak", (group["start"] + group["end"]) / 2)), 3),
                "score": score,
                "score_components": score_components,
                "evidence_labels": labels,
                "preferred_view": preferred_view,
                "viewing_path": [],
                "event_evidence": events,
                "face_review_candidates": faces,
                "dialogue_candidates": dialogues,
                "evidence_frames": [],
            }
        candidate["viewing_path"] = derive_viewing_path(
            candidate,
            face_data.get("samples", []),
            face_data.get("scan_width", 1280),
            face_data.get("scan_height", 720),
        )
        candidates.append(candidate)
    candidates.sort(key=lambda item: (-item["score"], item["start"], item["end"]))
    for rank, candidate in enumerate(candidates, start=1):
        candidate["rank"] = rank
    return candidates


def attach_evidence_frames(candidates, frames):
    """Attach extracted frame records to candidates by the stable event-order identifier."""
    for candidate, frame_group in zip(candidates, frames):
        candidate["evidence_frames"] = frame_group
    return candidates


def attach_event_frames(candidates, frames):
    """Attach flat extracted-frame records using the stable candidate event order."""
    grouped = [[] for _ in candidates]
    for frame in frames:
        grouped[int(frame["event_id"].split("-")[-1]) - 1].append(frame)
    return attach_evidence_frames(candidates, grouped)


def extract_candidate_frames(video, candidates, evidence_dir):
    """Extract start/peak/end views only for retained candidates."""
    from extract_360_views import extract_360_views

    return attach_event_frames(candidates, extract_360_views(video, candidates, evidence_dir))


def render_report(candidates):
    """Render a compact, review-oriented Markdown report."""
    lines = ["# 视频筛片候选", "", "姓名均为人脸匹配复核候选，不是自动确认。", ""]
    for candidate in candidates:
        lines.extend(
            [
                f"## 候选 {candidate['rank']} — {format_time(candidate['start'])} 至 {format_time(candidate['end'])}",
                "",
                f"- 排序分数：{candidate['score']}；首选观看方向：`{candidate['preferred_view']}`",
                f"- 证据：{', '.join(candidate['evidence_labels']) or '无'}",
            ]
        )
        for face in candidate["face_review_candidates"]:
            lines.append(f"- 人脸复核候选：{face['person']}（峰值相似度 {face['peak_score']:.3f}）")
        for dialogue in candidate["dialogue_candidates"]:
            lines.append(f"- 质量门已通过的原始对话：{dialogue.get('raw_text', '')}")
        for frame in candidate["evidence_frames"]:
            lines.append(f"- 证据帧：[{frame['role']} / {frame['view']}]({frame['path']})")
        lines.append("")
    return "\n".join(lines) + "\n"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events-json", required=True, type=Path)
    parser.add_argument("--faces-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--dialogue-json", type=Path)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        raise FileExistsError("Refusing to overwrite an existing candidate manifest or report")
    candidates = build_candidates(
        load_json(args.events_json),
        load_json(args.faces_json),
        load_json(args.dialogue_json) if args.dialogue_json else None,
    )
    if bool(args.video) != bool(args.evidence_dir):
        raise ValueError("--video and --evidence-dir must be provided together")
    if args.video:
        extract_candidate_frames(args.video, candidates, args.evidence_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(candidates), encoding="utf-8")
    print(json.dumps({"candidates": len(candidates)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
