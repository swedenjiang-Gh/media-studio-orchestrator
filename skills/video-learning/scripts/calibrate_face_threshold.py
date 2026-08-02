"""Estimate a conservative review threshold from a labeled local face reference library."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def choose_review_threshold(impostor_scores, minimum=0.5, quantile=0.995):
    """Keep review candidates above the selected cross-person impostor-score percentile."""
    if not impostor_scores:
        return minimum
    return max(float(minimum), float(np.quantile(impostor_scores, quantile)) + 0.001)


def load_reference(reference_dir):
    reference_dir = Path(reference_dir)
    embeddings = np.load(reference_dir / "reference-library.npz")["embeddings"]
    entries = json.loads((reference_dir / "reference-library.json").read_text(encoding="utf-8"))
    if len(embeddings) != len(entries):
        raise ValueError("reference library embeddings and metadata do not have equal lengths")
    return embeddings, [entry["person"] for entry in entries]


def calibrate(embeddings, people, max_per_person=25, top_k=5):
    """Hold out labeled samples and compare their true-person and strongest impostor scores."""
    groups = defaultdict(list)
    for index, person in enumerate(people):
        groups[person].append(index)
    group_indices = {person: np.asarray(indices) for person, indices in groups.items()}
    selected = []
    for indices in group_indices.values():
        stride = max(1, len(indices) // max_per_person)
        selected.extend(indices[::stride][:max_per_person])

    positives = []
    impostors = []
    for index in selected:
        similarities = embeddings @ embeddings[index]
        similarities[index] = -np.inf
        scores = {}
        for person, indices in group_indices.items():
            values = similarities[indices]
            values = values[np.isfinite(values)]
            if len(values):
                scores[person] = float(np.mean(np.sort(values)[-top_k:]))
        person = people[index]
        if person not in scores:
            continue
        positives.append(scores[person])
        impostors.append(max(score for name, score in scores.items() if name != person))
    return positives, impostors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-per-person", type=int, default=25)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing threshold calibration: {args.output}")
    embeddings, people = load_reference(args.reference_dir)
    positives, impostors = calibrate(embeddings, people, args.max_per_person, args.top_k)
    threshold = choose_review_threshold(impostors)
    result = {
        "sample_count": len(positives),
        "positive_score_percentiles": {str(p): round(float(np.quantile(positives, p)), 6) for p in (0.05, 0.5, 0.95)},
        "impostor_score_percentiles": {str(p): round(float(np.quantile(impostors, p)), 6) for p in (0.5, 0.95, 0.995)},
        "review_threshold": round(threshold, 6),
        "meaning": "review candidate only; a threshold cannot confirm identity without video evidence review",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
