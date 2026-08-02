# Video Screening Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce evidence-backed 360 and flat-video screening outputs: ranked review candidates, retained 360 master clips, 1080p reframed viewing clips, and a Markdown report.

**Architecture:** Project a stitched 360 source into four overlapping flat views and scan each timeline with the existing CUDA face runtime. Merge face continuity with event and dialogue evidence into one review-only candidate manifest. Render every approved candidate twice: an untouched-direction 360 master and a separate H.265 viewing copy whose yaw/pitch path is smoothed from the strongest visible view.

**Tech Stack:** Python 3.13, FFmpeg `v360`/`sendcmd`, HEVC NVENC, OpenCV-compatible NumPy frames, InsightFace CUDA runtime, Faster-Whisper outputs, unittest.

## Global Constraints

- Preserve input video and raw `.insv`; create new work/output directories only.
- Retain every 360 master as 2:1 equirectangular H.265/AAC.
- Create each reframed viewing copy as 1920x1080 H.265 at 20 Mbps with original audio.
- Person names are review candidates only; no score confirms identity automatically.
- Reject poor raw ASR from dialogue conclusions; never assign a speaker without independent voice or mouth-motion evidence.
- Treat `C:\Users\J\Pictures\Lightroom\1531\1531` as the sole default catalog root on this workstation.

---

### Task 1: 360 multi-view face scan

**Files:**
- Create: `scripts/scan_360_known_faces.py`
- Create: `tests/test_scan_360_known_faces.py`
- Modify: `SKILL.md`

**Interfaces:**
- Consumes: stitched 2:1 source, reference library, calibrated threshold.
- Produces: `{source, views, samples, review_candidates}` JSON. Each sample has `time`, `view`, detected face facts, and only review-level identity.

- [x] Write tests for the four-view CUDA `v360` filter and for view-aware continuous candidate grouping.
- [x] Run the new tests and verify they fail because the module is absent.
- [x] Implement one FFmpeg decode pipe per view and reuse the existing CUDA face runtime/identity boundary.
- [x] Run the new tests and a 10-second real 360 smoke scan.

### Task 2: Candidate fusion, ranking, evidence frames, and report

**Files:**
- Create: `scripts/build_screening_candidates.py`
- Create: `tests/test_build_screening_candidates.py`
- Modify: `SKILL.md`

**Interfaces:**
- Consumes: event JSON, 360-face scan JSON, optional dialogue JSON.
- Produces: `candidates.json` with source interval, peak, evidence labels, score components, preferred viewing direction, and `screening-report.md` with linked frames.

- [x] Write tests covering interval merging, conservative scoring, and the absence of dialogue claims when the quality gate fails.
- [x] Run the new tests and verify they fail because the module is absent.
- [x] Implement deterministic interval fusion and call `extract_360_views.py` only for retained candidates.
- [x] Generate a Markdown report with timestamps, evidence labels, output placeholders, and frame links.
- [x] Run tests and a real-source manifest/report smoke test.

### Task 3: Candidate master and reframed exports

**Files:**
- Create: `scripts/render_reframed_candidates.py`
- Create: `tests/test_render_reframed_candidates.py`
- Modify: `scripts/export_candidate_clips.py`
- Modify: `SKILL.md`

**Interfaces:**
- Consumes: candidate manifest with `start`, `end`, and `viewing_path` keyframes.
- Produces: exact 360-master clip paths and 1920x1080 H.265/AAC reframed clip paths.

- [x] Write tests for yaw unwrapping/smoothing and for the FFmpeg `sendcmd` + `v360` export command.
- [x] Run the tests and verify they fail because the module is absent.
- [x] Implement bounded yaw/pitch interpolation and the 20 Mbps NVENC viewing export.
- [x] Reuse the existing master exporter and append actual paths to the manifest without overwriting anything.
- [x] Run unit tests plus one real candidate render; inspect stream metadata and representative frame.

### Task 4: Batch orchestrator and quality boundaries

**Files:**
- Create: `scripts/screen_video_batch.py`
- Create: `tests/test_screen_video_batch.py`
- Modify: `references/v2-pending-design.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: one or more flat/stiched-360 video paths, shared references, optional dialogue manifests.
- Produces: one isolated output directory per source and a combined batch manifest with `complete`, `partial`, or `blocked` status.

- [x] Write tests for input routing, output-directory isolation, and a speaker-attribution block when no independent evidence is supplied.
- [x] Run the tests and verify they fail because the module is absent.
- [x] Implement orchestration that invokes only verified routes and reports unavailable prerequisites rather than guessing.
- [x] Mark speaker attribution blocked until clean speaker reference audio or validated mouth-motion evidence is supplied.
- [x] Run the whole suite, skill validation, and one real 360 end-to-end batch.

### Task 5: Documentation and release verification

**Files:**
- Modify: `README.md`, `SKILL.md`, `references/v2-pending-design.md`
- Test: `tests/test_skill_contract.py`, `tests/test_skill_360_contract.py`

- [x] Move only real, tested delivery behavior into `SKILL.md`.
- [x] Keep unresolved speaker attribution and SDK-vs-Studio comparison as explicit dependencies.
- [x] Run `python -m unittest discover -s tests -p "test_*.py"`, skill validation with `PYTHONUTF8=1`, and `git diff --check`.
- [ ] Commit and push the finished, verified implementation.
