"""Score known faces and group continuous appearances into review candidates."""

from collections import defaultdict

import numpy as np


def score_people(embedding, reference_embeddings, reference_people, top_k=5):
    """Return a per-person mean of the strongest cosine similarities."""
    query = np.asarray(embedding, dtype=np.float32)
    norm = np.linalg.norm(query)
    if not np.isfinite(norm) or norm == 0:
        raise ValueError("embedding must have a finite non-zero norm")
    query = query / norm
    references = np.asarray(reference_embeddings, dtype=np.float32)
    if len(references) != len(reference_people):
        raise ValueError("reference embeddings and people must have equal lengths")
    similarities = references @ query
    grouped = defaultdict(list)
    for person, similarity in zip(reference_people, similarities):
        grouped[person].append(float(similarity))
    return {
        person: float(np.mean(sorted(values, reverse=True)[:top_k]))
        for person, values in grouped.items()
    }


def group_face_samples(samples, max_gap_seconds, sample_interval_seconds):
    """Group time-adjacent person matches and retain the best evidence time for each interval."""
    ordered = sorted(samples, key=lambda sample: (sample["person"], sample["time"]))
    groups = []
    for sample in ordered:
        if (
            groups
            and groups[-1]["person"] == sample["person"]
            and sample["time"] - groups[-1]["last_time"] <= max_gap_seconds
        ):
            groups[-1]["samples"].append(sample)
            groups[-1]["last_time"] = sample["time"]
        else:
            groups.append({"person": sample["person"], "last_time": sample["time"], "samples": [sample]})

    intervals = []
    for group in groups:
        samples = group["samples"]
        peak = max(samples, key=lambda sample: (sample["score"], sample["face_pixels"]))
        intervals.append(
            {
                "person": group["person"],
                "start": samples[0]["time"],
                "end": samples[-1]["time"] + sample_interval_seconds,
                "peak": peak["time"],
                "peak_score": peak["score"],
                "peak_face_pixels": peak["face_pixels"],
                "sample_count": len(samples),
            }
        )
    return intervals
