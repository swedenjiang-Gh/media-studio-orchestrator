"""Persistent V2 queue state and audio-to-video timeline alignment."""

import argparse
import json
import sys
from pathlib import Path


STATE_VERSION = 3


def create_batch(sources):
    """Create an ordered, persistent batch state from supplied sources."""
    return {
        "version": STATE_VERSION,
        "jobs": [
            {
                "id": f"job-{index:04d}",
                "source": source,
                "status": "queued",
                "attempts": 0,
                "checkpoints": [],
                "capture_segments": [],
            }
            for index, source in enumerate(sources, start=1)
        ],
    }


def claim_next_job(batch, now):
    """Mark and return the first queued job, or return None when the batch is empty."""
    for job in batch["jobs"]:
        if job["status"] == "queued":
            job["status"] = "running"
            job["started_at"] = now
            job["last_progress_at"] = now
            return job
    return None


def add_checkpoint(job, media_time, observed_at):
    """Record a browser/player observation for recovery and later time alignment."""
    checkpoint = {"media_time": media_time, "observed_at": observed_at}
    segments = job.get("capture_segments", [])
    if segments:
        checkpoint["segment_id"] = segments[-1]["id"]
        segments[-1]["checkpoints"].append(checkpoint)
    job["checkpoints"].append(checkpoint)
    job["last_progress_at"] = observed_at
    return checkpoint


def begin_capture_segment(job, audio_started_at, media_time, observed_at, reason="initial"):
    """Close any active capture segment and begin an independently aligned one."""
    segments = job.setdefault("capture_segments", [])
    if segments and "ended_at" not in segments[-1]:
        segments[-1]["ended_at"] = observed_at
    segment = {
        "id": f"segment-{len(segments) + 1:03d}",
        "audio_started_at": audio_started_at,
        "reason": reason,
        "started_at": observed_at,
        "checkpoints": [],
    }
    segments.append(segment)
    add_checkpoint(job, media_time, observed_at)
    return segment


def has_unexpected_time_jump(previous, current, playback_rate=1.0, tolerance_seconds=2.0):
    """Return whether two playing-state observations indicate a seek rather than normal playback."""
    elapsed = current["observed_at"] - previous["observed_at"]
    expected_media_advance = elapsed * playback_rate
    actual_media_advance = current["media_time"] - previous["media_time"]
    return abs(actual_media_advance - expected_media_advance) > tolerance_seconds


def latest_resume_point(job):
    """Return the latest confirmed media time from the active or most recent segment."""
    segments = job.get("capture_segments", [])
    if segments and segments[-1]["checkpoints"]:
        return segments[-1]["checkpoints"][-1]["media_time"]
    if job.get("checkpoints"):
        return job["checkpoints"][-1]["media_time"]
    return None


def requeue_stalled_jobs(batch, now, timeout, max_attempts=None):
    """Return stale running jobs to the queue and count the jobs changed."""
    changed = 0
    for job in batch["jobs"]:
        if job["status"] == "running" and now - job["last_progress_at"] >= timeout:
            job["attempts"] += 1
            job["last_error"] = "playback_progress_timeout"
            job["status"] = "blocked" if max_attempts is not None and job["attempts"] >= max_attempts else "queued"
            changed += 1
    return changed


def fit_timeline_alignment(audio_started_at, observations):
    """Fit media_time = rate * (observed_at - audio_started_at) + offset."""
    if not observations:
        raise ValueError("at least one playback observation is required")

    samples = [
        (item["observed_at"] - audio_started_at, item["media_time"])
        for item in observations
    ]
    if len(samples) == 1:
        rate = 1.0
        offset = samples[0][1] - samples[0][0]
    else:
        mean_x = sum(sample[0] for sample in samples) / len(samples)
        mean_y = sum(sample[1] for sample in samples) / len(samples)
        denominator = sum((x - mean_x) ** 2 for x, _ in samples)
        if denominator == 0:
            raise ValueError("playback observations need distinct observation times")
        rate = sum((x - mean_x) * (y - mean_y) for x, y in samples) / denominator
        offset = mean_y - rate * mean_x

    def media_time_at(observed_at):
        return rate * (observed_at - audio_started_at) + offset

    return {
        "audio_started_at": audio_started_at,
        "offset_seconds": offset,
        "rate": rate,
        "media_time_at": media_time_at,
    }


def store_timeline_alignment(job, audio_started_at):
    """Store a JSON-safe alignment fitted from a job's recorded playback checkpoints."""
    fitted = fit_timeline_alignment(audio_started_at, job["checkpoints"])
    alignment = {
        "audio_started_at": fitted["audio_started_at"],
        "offset_seconds": fitted["offset_seconds"],
        "rate": fitted["rate"],
    }
    job["timeline_alignment"] = alignment
    return alignment


def store_segment_alignments(job):
    """Store one JSON-safe timeline alignment for every independent capture segment."""
    alignments = []
    for segment in job.get("capture_segments", []):
        fitted = fit_timeline_alignment(segment["audio_started_at"], segment["checkpoints"])
        alignments.append(
            {
                "segment_id": segment["id"],
                "audio_started_at": fitted["audio_started_at"],
                "offset_seconds": fitted["offset_seconds"],
                "rate": fitted["rate"],
            }
        )
    job["timeline_alignments"] = alignments
    return alignments


def load_state(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, batch):
    Path(path).write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    from list_media import write_manifest

    parser = argparse.ArgumentParser(description="Manage a video-learning V2 batch queue.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("state")
    init.add_argument("sources", nargs="+")
    claim = subparsers.add_parser("claim")
    claim.add_argument("state")
    claim.add_argument("--now", type=float, required=True)
    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("state")
    checkpoint.add_argument("job_id")
    checkpoint.add_argument("--media-time", type=float, required=True)
    checkpoint.add_argument("--observed-at", type=float, required=True)
    segment = subparsers.add_parser("segment")
    segment.add_argument("state")
    segment.add_argument("job_id")
    segment.add_argument("--audio-started-at", type=float, required=True)
    segment.add_argument("--media-time", type=float, required=True)
    segment.add_argument("--observed-at", type=float, required=True)
    segment.add_argument("--reason", default="initial")
    requeue = subparsers.add_parser("requeue-stalled")
    requeue.add_argument("state")
    requeue.add_argument("--now", type=float, required=True)
    requeue.add_argument("--timeout", type=float, required=True)
    requeue.add_argument("--max-attempts", type=int)
    align = subparsers.add_parser("align")
    align.add_argument("state")
    align.add_argument("job_id")
    align.add_argument("--audio-started-at", type=float, required=True)
    resume = subparsers.add_parser("resume-point")
    resume.add_argument("state")
    resume.add_argument("job_id")

    args = parser.parse_args()
    if args.command == "init":
        target = Path(args.state)
        if target.exists():
            raise SystemExit(f"state already exists: {target}")
        save_state(target, create_batch(args.sources))
        return

    batch = load_state(args.state)
    if args.command == "claim":
        job = claim_next_job(batch, args.now)
        save_state(args.state, batch)
        write_manifest(job, sys.stdout)
    elif args.command == "checkpoint":
        job = next((item for item in batch["jobs"] if item["id"] == args.job_id), None)
        if job is None:
            raise SystemExit(f"unknown job: {args.job_id}")
        add_checkpoint(job, args.media_time, args.observed_at)
        save_state(args.state, batch)
    elif args.command == "segment":
        job = next((item for item in batch["jobs"] if item["id"] == args.job_id), None)
        if job is None:
            raise SystemExit(f"unknown job: {args.job_id}")
        result = begin_capture_segment(job, args.audio_started_at, args.media_time, args.observed_at, args.reason)
        save_state(args.state, batch)
        write_manifest(result, sys.stdout)
    elif args.command == "requeue-stalled":
        print(requeue_stalled_jobs(batch, args.now, args.timeout, args.max_attempts))
        save_state(args.state, batch)
    elif args.command == "align":
        job = next((item for item in batch["jobs"] if item["id"] == args.job_id), None)
        if job is None:
            raise SystemExit(f"unknown job: {args.job_id}")
        alignment = store_segment_alignments(job) if job.get("capture_segments") else store_timeline_alignment(job, args.audio_started_at)
        save_state(args.state, batch)
        write_manifest(alignment, sys.stdout)
    else:
        job = next((item for item in batch["jobs"] if item["id"] == args.job_id), None)
        if job is None:
            raise SystemExit(f"unknown job: {args.job_id}")
        write_manifest({"media_time": latest_resume_point(job)}, sys.stdout)


if __name__ == "__main__":
    main()
