import unittest

from scripts.check_capture import parse_dshow_audio_devices
from scripts.extract_360_views import build_view_manifest, v360_filter
from scripts.extract_event_frames import event_frame_manifest
from scripts.inspect_media import classify_insta360
from scripts import scan_events
from scripts.scan_events import build_event_intervals
from scripts.v2_state import (
    add_checkpoint,
    begin_capture_segment,
    claim_next_job,
    create_batch,
    fit_timeline_alignment,
    has_unexpected_time_jump,
    latest_resume_point,
    requeue_stalled_jobs,
    store_segment_alignments,
    store_timeline_alignment,
)


class V2StateTests(unittest.TestCase):
    def test_queue_claims_one_job_checkpoints_it_and_requeues_a_stall(self):
        batch = create_batch(["D:/clips/a.mp4", "https://example.test/b"])

        job = claim_next_job(batch, now=100.0)
        self.assertEqual(job["status"], "running")
        self.assertEqual(job["source"], "D:/clips/a.mp4")
        add_checkpoint(job, media_time=42.5, observed_at=101.0)
        self.assertEqual(job["checkpoints"], [{"media_time": 42.5, "observed_at": 101.0}])

        self.assertEqual(requeue_stalled_jobs(batch, now=130.0, timeout=20.0), 1)
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["attempts"], 1)

    def test_queue_blocks_a_job_after_its_final_retry(self):
        batch = create_batch(["D:/clips/a.mp4"])
        job = claim_next_job(batch, now=100.0)

        self.assertEqual(requeue_stalled_jobs(batch, now=130.0, timeout=20.0, max_attempts=1), 1)
        self.assertEqual(job["status"], "blocked")
        self.assertEqual(job["attempts"], 1)

    def test_alignment_uses_multiple_observations_to_estimate_offset_and_drift(self):
        alignment = fit_timeline_alignment(
            audio_started_at=100.0,
            observations=[
                {"observed_at": 110.0, "media_time": 8.0},
                {"observed_at": 130.0, "media_time": 28.0},
            ],
        )

        self.assertAlmostEqual(alignment["offset_seconds"], -2.0)
        self.assertAlmostEqual(alignment["rate"], 1.0)
        self.assertAlmostEqual(alignment["media_time_at"](150.0), 48.0)

    def test_alignment_is_stored_as_json_safe_job_metadata(self):
        job = {"checkpoints": [{"observed_at": 110.0, "media_time": 8.0}]}

        alignment = store_timeline_alignment(job, audio_started_at=100.0)

        self.assertEqual(alignment, {"audio_started_at": 100.0, "offset_seconds": -2.0, "rate": 1.0})
        self.assertEqual(job["timeline_alignment"], alignment)

    def test_seek_creates_an_independently_aligned_segment_and_preserves_resume_point(self):
        job = {"checkpoints": []}
        begin_capture_segment(job, audio_started_at=100.0, media_time=0.0, observed_at=101.0)
        first_checkpoint = add_checkpoint(job, media_time=8.0, observed_at=109.0)

        self.assertTrue(
            has_unexpected_time_jump(first_checkpoint, {"media_time": 40.0, "observed_at": 110.0})
        )
        second = begin_capture_segment(
            job,
            audio_started_at=110.0,
            media_time=40.0,
            observed_at=110.0,
            reason="seek_detected",
        )
        add_checkpoint(job, media_time=50.0, observed_at=120.0)

        self.assertEqual(len(job["capture_segments"]), 2)
        self.assertEqual(second["reason"], "seek_detected")
        self.assertEqual(latest_resume_point(job), 50.0)
        self.assertEqual(
            store_segment_alignments(job),
            [
                {"segment_id": "segment-001", "audio_started_at": 100.0, "offset_seconds": -1.0, "rate": 1.0},
                {"segment_id": "segment-002", "audio_started_at": 110.0, "offset_seconds": 40.0, "rate": 1.0},
            ],
        )


class V2MediaTests(unittest.TestCase):
    def test_gpu_coarse_scan_uses_cuda_scaling_and_two_fps_sampling(self):
        self.assertTrue(hasattr(scan_events, "build_scan_command"))
        command = scan_events.build_scan_command(
            "D:/clips/360.mp4",
            ffmpeg="ffmpeg",
            scan_width=160,
            scan_height=80,
            scan_fps=2.0,
            hwaccel="cuda",
        )

        self.assertIn("-hwaccel", command)
        self.assertIn("cuda", command)
        self.assertIn(
            "scale_cuda=160:80,hwdownload,format=nv12,format=gray,fps=2",
            command,
        )

    def test_insta360_without_equirectangular_metadata_requires_studio_export(self):
        result = classify_insta360(
            "D:/clips/VID_001.insv",
            {"streams": [{"codec_type": "video", "width": 5760, "height": 2880, "tags": {}}]},
        )

        self.assertEqual(result["kind"], "raw_or_unknown_insv")
        self.assertTrue(result["requires_studio_export"])

    def test_insta360_equirectangular_stream_can_be_analyzed_directly(self):
        result = classify_insta360(
            "D:/clips/VID_001.insv",
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 5760,
                        "height": 2880,
                        "tags": {"projection": "equirectangular"},
                    }
                ]
            },
        )

        self.assertEqual(result["kind"], "stitched_360")
        self.assertFalse(result["requires_studio_export"])

    def test_event_intervals_group_change_peaks_without_using_fixed_coverage_frames(self):
        intervals = build_event_intervals(
            scores=[0.1, 0.2, 8.0, 10.0, 1.0, 0.1],
            fps=2.0,
            threshold=5.0,
            padding_seconds=0.5,
        )

        self.assertEqual(len(intervals), 1)
        self.assertAlmostEqual(intervals[0]["start"], 0.5)
        self.assertAlmostEqual(intervals[0]["peak"], 1.5)
        self.assertAlmostEqual(intervals[0]["end"], 2.5)

    def test_event_intervals_merge_short_low_change_gaps_inside_one_event(self):
        intervals = build_event_intervals(
            scores=[0.1, 8.0, 0.2, 0.1, 10.0, 0.1],
            fps=2.0,
            threshold=5.0,
            padding_seconds=0.5,
        )

        self.assertEqual(len(intervals), 1)
        self.assertAlmostEqual(intervals[0]["start"], 0.0)
        self.assertAlmostEqual(intervals[0]["peak"], 2.0)
        self.assertAlmostEqual(intervals[0]["end"], 3.0)

    def test_event_intervals_merge_overlapping_padding_windows(self):
        intervals = build_event_intervals(
            scores=[0.1, 8.0, 0.1, 10.0, 0.1],
            fps=2.0,
            threshold=5.0,
            padding_seconds=0.5,
            merge_gap_seconds=0.0,
        )

        self.assertEqual(len(intervals), 1)
        self.assertAlmostEqual(intervals[0]["start"], 0.0)
        self.assertAlmostEqual(intervals[0]["peak"], 1.5)
        self.assertAlmostEqual(intervals[0]["end"], 2.5)

    def test_event_frame_manifest_keeps_start_peak_and_end_for_each_event(self):
        frames = event_frame_manifest(
            [{"start": 10.0, "peak": 12.5, "end": 15.0}],
            "D:/work/events",
        )

        self.assertEqual(
            frames,
            [
                {"event_id": "event-001", "role": "start", "time": 10.0, "path": "D:/work/events/event-001-start.jpg"},
                {"event_id": "event-001", "role": "peak", "time": 12.5, "path": "D:/work/events/event-001-peak.jpg"},
                {"event_id": "event-001", "role": "end", "time": 15.0, "path": "D:/work/events/event-001-end.jpg"},
            ],
        )

    def test_360_view_manifest_uses_overlapping_horizon_views_at_each_event_evidence_time(self):
        frames = build_view_manifest(
            [{"start": 10.0, "peak": 12.5, "end": 15.0}],
            "D:/work/360-events",
        )

        self.assertEqual(len(frames), 12)
        self.assertEqual(
            frames[0],
            {
                "event_id": "event-001",
                "role": "start",
                "view": "front",
                "time": 10.0,
                "path": "D:/work/360-events/event-001-start-front.jpg",
            },
        )
        self.assertEqual({frame["view"] for frame in frames}, {"front", "right", "back", "left"})

    def test_360_view_manifest_adds_vertical_views_only_when_requested(self):
        frames = build_view_manifest(
            [{"start": 10.0, "peak": 12.5, "end": 15.0}],
            "D:/work/360-events",
            include_vertical=True,
        )

        self.assertEqual(len(frames), 18)
        self.assertEqual({frame["view"] for frame in frames}, {"front", "right", "back", "left", "up", "down"})

    def test_360_filter_projects_equirectangular_input_to_a_flat_overlapping_view(self):
        self.assertEqual(
            v360_filter("right", width=1280, height=720),
            "v360=input=equirect:output=flat:yaw=90:pitch=0:h_fov=100:v_fov=75:w=1280:h=720",
        )


class V2CaptureTests(unittest.TestCase):
    def test_directshow_audio_parser_finds_verified_vb_cable_device(self):
        devices = parse_dshow_audio_devices(
            '[dshow] DirectShow audio devices\n[dshow]  "CABLE Output (VB-Audio Virtual Cable)" (audio)\n'
        )

        self.assertEqual(devices, ["CABLE Output (VB-Audio Virtual Cable)"])

    def test_directshow_audio_parser_tolerates_non_utf8_ffmpeg_bytes(self):
        devices = parse_dshow_audio_devices(
            b'[dshow] \x8e\xff\n[dshow]  "CABLE Output (VB-Audio Virtual Cable)" (audio)\n'
        )

        self.assertEqual(devices, ["CABLE Output (VB-Audio Virtual Cable)"])


if __name__ == "__main__":
    unittest.main()
