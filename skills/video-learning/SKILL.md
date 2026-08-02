---
name: video-learning
description: Use when a user provides local videos, folders, public video URLs, authorized online playback, or Insta360 footage and asks to understand content, create Chinese learning notes, screen clips, make evidence-based rough cuts, find people or dialogue candidates, or extract information.
---

# 视频理解、筛片、粗剪与信息提取（Video Understanding, Screening, Rough Cutting, and Learning）

Create evidence-based video understanding, screening, and information-extraction results. The default contract is learning notes and a summary. Rough cutting, face recognition, new external subtitles, and translation are opt-in only: run them only when the user explicitly asks. Never claim that a video was watched, transcribed, OCRed, or visually analyzed unless its content was actually accessible and processed.

## Select the delivery contract

Before expensive processing, classify the requested result.

| User request | Deliver |
|---|---|
| Learn, understand, summarize, extract information | Streams, preserved existing captions, and only the audio/visual/OCR evidence needed for notes and a summary. Do not create candidates, run face recognition, write a new SRT, or translate. |
| Screen, rough cut, highlights, dialogue segments | Event/dialogue evidence and review candidates; export derived clips only when requested. |
| External subtitles, subtitles, bilingual subtitles, translation | A new SRT; translate only when bilingual subtitles or translation is explicitly requested. Preserve source-language lines and mark incomplete translation `partial`. |
| Family video: named person, complete face visibility, find me/child | Calibrated face-reference review candidates in addition to the requested screening delivery; never assert identity automatically. |
| Insta360 | Preserve raw `.insv` and use a stitched 2:1 master. On explicit screening, identify highlights/dialogue only; do not search for continuous face-in-frame evidence. Use Studio Deep Track for stable reframing unless a local SDK continuous-tracking API has been verified. |

## Start

1. Identify the batch inputs: URLs, multiple local video files, folders, or a mixture.
2. Run `scripts/check_runtime.py` before choosing a local workflow. It is read-only.
3. Expand every local path with `scripts/list_media.py`. It recursively lists supported videos from folders and returns `media`, `missing`, and `ignored`; keep URLs as separate queue items.
4. Deduplicate the combined queue. Process only the supplied URLs and local media, and keep missing or unsupported inputs for the final blocked-items report.
5. Select the source route for each item before expensive work.

## Process the batch

Treat a batch as complete only when every accessible item has reached its requested delivery contract or has a concrete blocked/partial reason. Do not emit per-item download-complete messages or wait for the user to ask for the next stage.

Use this order for each item after selecting the delivery contract:

1. Use an existing complete local video, or obtain an authorized complete local copy with `download-videos`.
2. Inspect streams, then preserve subtitles and extract full timestamped audio.
3. Collect only the evidence required by that contract. Build event intervals and candidate frames only for screening/rough-cut delivery; run face recognition only for an explicit named-person/complete-visibility request; write a new SRT or translation only for an explicit subtitle/translation request.
4. Apply the applicable quality gate, cross-check evidence, then build the requested learning, screening, rough-cut, subtitle, or extraction result.

## Route the source

| Source state | Route |
|---|---|
| Accessible local video | Inspect streams with `ffprobe`, then collect embedded subtitles, audio transcription, timed keyframes, OCR, and local visual understanding in parallel when each source is available. |
| Public URL whose complete video can be saved with authorization | Prefer a complete local copy with `download-videos`, then process the saved video as a local source. |
| Raw Insta360 `.insv` | Preserve the original. If `ffprobe` shows an already stitched equirectangular stream, process it as a local 360 video. Otherwise, use the official **Desktop Media SDK** only when its SDK root and compiled official Demo are present and the SDK route is verified for the source file; use `scripts/insta360_sdk_frames.py` for selected-frame stitching. Full-video export is verified separately on this workstation; bounded-interval SDK export is not. Otherwise use Insta360 Studio. |
| Playable webpage whose complete video cannot be saved | Preserve available captions; capture authorized playback audio through the verified per-app route and collect time-coded page frames, OCR, and visual observations. Mark visual coverage as partial. |
| Login-only webpage | Use only the user's authorized session. Prefer an authorized complete local copy; otherwise use page-provided captions or verified playback capture. |
| DRM, paid-wall, blocked, or inaccessible media | Stop and explain the access boundary. Offer platform-exported captions, a user-provided file, or user-provided notes. |

Do not bypass login, payment, DRM, regional restrictions, or anti-automation controls. Do not automatically read browser cookies. For this user's video-learning workflow, a request to download or learn a supplied video includes permission to save an accessible local copy; do not ask a second download-confirmation question.

Prefer a complete local video whenever it is authorized and obtainable: it preserves full-resolution frames, embedded subtitles, audio, stream metadata, reproducible timecodes, and later re-analysis. Do not default to an audio-only stream; use it only when the user explicitly requests an audio-only quick note or a complete local video is unavailable.

When a request is to learn, understand, screen, or extract from a video, continue from a successful local download directly into inspection and evidence extraction. Report only when access is blocked, a user decision is required, or the requested output is complete.

Treat multiple user-supplied URLs, local video files, and folders as one end-to-end batch. Process only those inputs, complete download and requested analysis for each accessible item without per-item confirmation, and return the final combined results together with a concise list of blocked or partial items.

## Reliability and 360 triage

For a V2 batch, create an explicit queue state under the batch work directory with `scripts/v2_state.py`. Record each supplied source as a job before processing; use `queued`, `running`, `complete`, `partial`, or `blocked` rather than silently abandoning a source.

- `Desktop Media SDK`: selected-frame export is verified; full-video export is verified on this 4090 workstation with MediaSDK 3.1.3.1 and a real raw `.insv`. The full export retained `3840x1920` equirectangular video, FlowState request, H.265 at approximately 60 Mbps, AAC audio, and the original 29:59.8 duration. For a supported source, use `scripts/insta360_sdk_frames.py` with the compiled official Demo, source frame indices, a new output directory, and a 2:1 output size. The current public header and Windows Demo does not expose a bounded MP4 interval export; do not represent selected-frame export as a direct clip-export API. A community CLI is only a reference, never a substitute for the verified SDK route. Preserve any retained 360 master as `2:1 equirectangular` with audio. Read `references/v2-pending-design.md` for the unresolved design and acceptance details.
- Before an authorized browser-playback capture, run `scripts/check_capture.py --verify` while the intended playback app is routed to VB-CABLE and playing. A visible device is not evidence of sound: continue only when the result has `available: true` and `has_signal: true`.
- Start every continuous recording with `scripts/v2_state.py segment`, including its first player `currentTime` and recording start. Use `checkpoint` for later observations in that same segment.
- While the player is visibly playing, compare consecutive `currentTime` observations against elapsed recording time. A material unexpected change indicates a user seek: stop that capture, begin a new capture segment at the new player position, and retain both segments. Do not join audio across a seek as if it were continuous.
- If observed `currentTime` stops advancing, use `scripts/v2_state.py resume-point` to obtain the saved checkpoint, requeue it with `scripts/v2_state.py requeue-stalled`, and resume only after the player state is visibly verified. After the configured maximum retry count, report the job as `blocked`; never fabricate a completed transcript from a stalled capture.
- Fit `currentTime` against each audio-recording segment with `scripts/v2_state.py align`. Use that segment's stored offset/rate for transcript, OCR, and screenshot timestamps; disclose any alignment based on fewer than two observations as provisional.
- For an `.insv`, run `scripts/inspect_media.py` first. `raw_or_unknown_insv` requires a high-quality, non-reframed stitched export before full visual/OCR analysis. Use the verified Desktop Media SDK selected-frame route to triage original inputs when available; use Studio when the source route or SDK executable is not verified. `stitched_360` may continue to event scanning and multi-view inspection. For a supplied raw `.insv` folder with a verified official Windows Demo, use `scripts/screen_insta360_folder.py`: it recursively enumerates sources, sequentially creates one independent `2:1` H.265/AAC master per source, then passes only successful masters into `screen_video_batch.py`. It records source-to-master-to-screening status in `insta360-folder-manifest.json`. Never merge unrelated recordings.
- Use a new `--output-root` for a fresh raw `.insv` folder run. If the host or process was interrupted after a master completed, use the same root with `--resume`; it reuses only the matching existing stitched master and creates a new `screening-resume-###` directory. Do not delete or overwrite old masters, screening directories, raw `.insv`, or the original folder.
- For an explicit screening or rough-cut delivery, run `scripts/scan_events.py` across the full timeline. On this 4090 workstation, prefer `--hwaccel cuda --scan-fps 2` for the first-pass GPU coarse scan; it downsizes only the change signal, not final evidence. Re-scan uncertain or high-activity candidate spans more densely before making a selection. For normal video, use `scripts/extract_event_frames.py` to obtain each event's start, peak, and end evidence frames. For stitched 360 video, use `scripts/extract_360_views.py` to project those evidence times into overlapping rectilinear views (`front`, `right`, `back`, `left`); add `--vertical` only when an event could contain relevant upward/downward activity. These event frames drive OCR and visual-model batches; do not replace them with fixed-interval sampling.
- Only for an explicit named-person or complete-face-visibility request, scan a stitched 360 timeline with `scripts/scan_360_known_faces.py` and the calibrated reference library. It GPU-decodes the source then projects the four overlapping horizon views before running the local face model; FFmpeg `v360` projection itself is CPU-side. Keep its names as `review_candidate` only and retain the view direction with every interval.
- For an explicit screening/rough-cut delivery, `scripts/screen_video_batch.py` runs the verified screening route end-to-end into a new per-source output directory: event scan, configured face evidence, `scripts/build_screening_candidates.py`, evidence frames, `360 master candidate` export, and `scripts/render_reframed_candidates.py` when applicable. It records every job as `complete`, `partial`, or `blocked`; feed raw unstitched `.insv` through `screen_insta360_folder.py` first rather than calling this script directly. Do not invoke it for ordinary learning.
- The batch preserves raw dialogue JSON when requested. Unless independent voice or mouth-motion evidence is supplied, write `speaker_attribution: blocked_missing_independent_voice_or_mouth_evidence`; never turn a face match or same-frame presence into a speaker claim.
- When an external-subtitle delivery is explicitly requested, write `source.srt` beside the per-source delivery and a same-name `.srt` beside every exported master/reframed candidate. Crop candidate subtitles from the preserved full transcript and rebase timecodes to each derived clip; do not transcribe the same audio again.
- For an explicitly requested bilingual subtitle or translation delivery, preserve the raw ASR `dialogue.json` and any accessible platform captions. Prefer a platform Chinese caption track as translation evidence after an explicit time-alignment check. Assemble ASR fragments into complete sentence/utterance units before writing a bilingual SRT; never use a fixed fragment count as a semantic boundary. For uncovered units, send the full unit with neighbouring context to the local translator and require complete numbered output plus the completion marker. Use a fixed local output ceiling of 512 first; if the marker or a numbered result is missing, retry only the affected intact unit at 1024. Never split a sentence by token count; if the intact retry remains incomplete, keep the source line and mark the delivery `partial`. Preserve source lines, detected language, caption source, and `quality_gate`. On a missing runtime, timeout, malformed result, partial result, or unresolved alignment, write the source line only and record the explicit `translation_status` in `delivery.json`; never invent a translation or use it as audio confirmation.

## Playback-capture fallback

Use this route only when the authorized page has no reusable audio stream and an approved per-app audio route has been verified. Continue visual, OCR, and subtitle evidence collection independently.

1. Start the recorder **before** seeking or starting playback; retain its start time as the audio-to-video offset.
2. Route only the browser/Codex app to the virtual playback device. Do not change the system-wide default output unless the user asks.
3. Start at the video beginning, keep normal playback unless a lower-accuracy speed-up is explicitly selected, and stop recording when the first playback pass ends so auto-loop audio is not retained.
4. Capture a page frame at the start, at detectable page/video changes, and at adaptively chosen coverage points inside long no-change spans; record the actual media `currentTime` beside each frame. Do not make a fixed interval the primary visual analysis.
5. Keep the raw recording. Trim any pre-roll or loop tail into a separate transcription input; disclose an uncertain offset rather than fabricating timecodes.

On this workstation, the verified route is `ChatGPT/Codex or Chrome output -> CABLE Input (VB-Audio Virtual Cable)` and FFmpeg recording from `CABLE Output (VB-Audio Virtual Cable)`. Route only the playback app; leave the system default speaker and unrelated apps unchanged. Read [references/runtime-setup.md](references/runtime-setup.md) for the local setup and validation details.

## Extract evidence

- Treat subtitles, audio transcription, OCR, and visual-language analysis as parallel evidence sources, not a fallback chain. Start all available sources for the same time ranges, then cross-check them before drafting.
- Keep timecodes on every transcript segment and frame.
- Build **event intervals** before sending frames to the visual model. Detect scene cuts, sustained motion or camera-direction changes, visible people/objects/screens, OCR/subtitle changes, and audio transitions when present. For every event interval, retain an entry frame, the most informative change/peak frame, and an exit frame with real timestamps.
- Use adaptive coverage only to bound uncertainty in spans with no detected event. Coverage density must depend on duration, motion level, source type, and the cost of missing a short event; it is not a fixed-interval primary analysis. When a sparse pass exposes uncertainty, re-scan that span more densely instead of accepting the gap.
- If a coarse scan finds no abrupt intervals on continuous-motion footage, do not conclude that there are no people, dialogue, or highlights. Select duration- and motion-aware coverage anchors, then use original-resolution views and audio evidence to decide whether a denser local re-scan is needed; never substitute a fixed 15-second cadence.
- For a stitched 360 video, detect events on the equirectangular stream and inspect overlapping rectilinear views around the horizon; add upward/downward views when activity could be above or below. Do not feed an unstitched dual-fisheye frame to OCR or the visual model as if it were a normal camera frame.
- Use OCR only when both the OCR package and engine are ready. Preserve ambiguous text as `[OCR uncertain]`; never repair commands from guesswork.
- Send chronological batches of keyframes to the local visual model. Ask it to describe only visible people, objects, screens, actions, changes, and uncertainty; do not ask it to infer identities, intent, dialogue, off-screen events, or unseen causes.
- Cross-check commands and settings against transcript, OCR, visible frames, and visual-model observations. Label each item `confirmed`, `partial`, `likely`, or `unverified`, and name the supporting source(s).
- If background playback capture is the only route, say that playback must advance and that silent operation depends on a verified audio route. Do not claim it is available merely because a browser can play the video.

## Transcription quality gate

1. Preserve the raw timestamped transcript; never overwrite it with a cleaned version.
2. Before drafting notes, inspect samples from the beginning, middle, and end for broken syntax, homophone substitutions, product names, and numbers.
3. If the samples are not semantically coherent, reject that transcript for final notes and rerun with a higher-quality recognizer. On this workstation, CUDA `float16` with `large-v3-turbo` is verified; `base` is only a preliminary-speed route.
4. Treat language-only cleanup as `semantic candidate`, not audio confirmation. Confirm a correction with a second audio pass or visible/OCR evidence; otherwise retain the raw wording and mark it uncertain.

## Evidence-led visual notes

When extracted frames materially support the learning result, insert a **small, decisive set of original keyframes** into the Markdown note instead of leaving all evidence only in a work folder.

- Place each frame immediately beside the conclusion it supports; caption it with the real timestamp and the directly visible fact.
- Prefer frames that show a named model/version, command, parameter, input/output, interface state, or failure case. Do not add a decorative gallery or repeat near-identical frames.
- Keep the absolute path to the original frame and retain the raw video. A frame proves only what is visibly present at that timestamp.
- Do not use ASR or visual-model output alone to confirm a proprietary name, model version, price, benchmark, count, success rate, or reliability claim. Confirm it with readable visible text/OCR or independent audio evidence; otherwise label it as an `author-reported claim` or `unverified`.
- If ASR, OCR, and visual observations disagree, preserve the raw wording, show the conflicting evidence, and do not normalize it into a fact.

## Video screening and candidate extraction

Use the same evidence index for learning and screening; do not run a shallow separate pass just because the requested output is a clip list.

When a user asks to recognize people named in Lightroom Classic, use only the user-specified Lightroom working directory as the catalog root. If no directory is supplied, read the local default and persistent reference-data root in `references/local-machine.md`; it is machine-private and must never be committed. Do not search parent directories, sibling catalog folders, or a remembered fallback path. `work` is disposable runtime output and must never hold the reusable people index or face-reference library. Before exporting, inspect `<persistent-reference-root>\people-index\README.md`: if it records that exact catalog path and all three CSV files are present, reuse that index; do not export it again. Otherwise resolve the single `.lrcat` directly inside the user-specified Lightroom working directory and create a new catalog-specific directory under persistent reference data with `scripts/export_lightroom_people_index.py` and SQLite read-only access. Preserve its `people-summary.csv`, `people-photos.csv`, and `people-faces.csv` as reference-library inputs. Build the same-model library at `<persistent-reference-root>\face-reference` with `scripts/build_face_reference.py`, calculate a conservative review threshold there with `scripts/calibrate_face_threshold.py`, then scan a normal or already reframed flat video with `scripts/scan_known_faces.py`. The scan emits raw review candidates, never confirmed names; for 360 video, first inspect the relevant overlapping rectilinear views instead of scanning the equirectangular frame as a flat video. On this workstation, initialize the GPU face runtime with `scripts/face_runtime.py` before loading models; its `create_face_analysis()` refuses a silent CPU fallback. The Python 3.13 InsightFace install intentionally omits only its optional 3D mask-rendering extension; standard detection, landmarks, age/gender, and 512-dimensional recognition embeddings remain available. Lightroom's stored face feature vectors are not interchangeable with a video recognition model: crop/export the labeled source faces and build a fresh, single-model embedding library before making name-based video decisions. Never write the Lightroom catalog or modify source photos.

For a stitched 360 source, keep a `360 master candidate` as the equirectangular picture and audio for every retained source interval. Create a separately encoded `reframed candidate` only after its person/event tracking and smooth viewing transform are verified; never substitute it for the 360 master. If that route is unavailable, return the master candidate and mark the reframed output `partial` rather than fabricating it.

- Build an event card for each retained interval: actual start/end/peak time, directly visible action or scene change, transcript/OCR evidence when available, representative-frame paths, and an evidence label.
- Use `scripts/build_screening_candidates.py` to merge full-timeline visual-change intervals, four-view face review candidates, and only `quality_gate: passed` dialogue records. It ranks review priorities with separately shown score components, keeps each candidate's strongest viewing direction, extracts start/peak/end evidence views only for retained candidates, and writes a Markdown review report. A rejected or missing transcript contributes no dialogue claim.
- Rank **精彩片段候选** by observable activity, interaction, speech, scene change, novelty, or user-specified criteria. Explain the evidence that makes a candidate worth reviewing; do not present a subjective "精彩" verdict as fact.
- Identify **互动/对话候选** from timestamped speech plus visible people/activity where available. Audio alone can establish spoken content but not who is visible; a visual frame can establish visible interaction but not dialogue content.
- Treat a relationship or identity supplied by the user as `user-provided context`. It may prioritize review (for example, "look for my child and me"), but never becomes an identity recognition claim from the visual model.
- For a requested candidate clip, use `scripts/export_candidate_clips.py` to export a derived, time-bounded **候选片段导出** with a small context lead-in/out. It is verified to create a H.265 `360 master candidate` with AAC audio retained; preserve the source path and exact source interval, and label it as a candidate rather than silently replacing the original. Keep the raw video untouched.
- For a stitched 360 candidate, use `scripts/render_reframed_candidates.py` to create its separately encoded `reframed candidate`. It takes the face-centred yaw/pitch path from the candidate manifest, densifies/smooths it, and exports `1920x1080` H.265 at 20 Mbps with original audio. It is a viewing copy; retain the paired 2:1 `360 master candidate` and disclose that face-centering is a review aid, not proof of identity or speaking.
- For an unstitched Insta360 recording, wait for a non-reframed stitched 360 export before ranking events or exporting candidates. For stitched 360, judge a candidate across its relevant overlapping views, not a single front view.
- Rank 360 rough-cut candidates from sustained clear face visibility, recognized-person evidence from the local reference library, interaction, speech activity, scene/action change, and novelty. A face match below the configured review threshold is `unverified`, not a name claim.
- Detect dialogue from timestamped speech and visible interaction. `speaker attribution` requires independent evidence such as voice identity or visible mouth/speech alignment; do not assign a spoken sentence to a named person from a face in the frame alone.
- Use `scripts/dialogue_candidates.py` with local `large-v3-turbo` CUDA and VAD to generate timestamped raw review candidates. Run the transcription quality gate before treating any recognized wording as a dialogue fact; wind, road noise, child speech, or repeated prompts can leave raw ASR unsuitable for final notes. Never infer a speaker from that transcript alone.

## Avoid these mistakes

- Do not treat normal playback as proof that a reusable subtitle or audio source is available.
- Do not treat a public URL as proof that it can be processed in the current environment.
- Do not turn OCR guesses or inferred commands into confirmed instructions.
- Do not turn visual-model inference into a confirmed fact. A single frame can confirm only what is directly visible; continuity-based event descriptions are normally `likely`.
- Do not make a background or silent-processing promise before verifying the source and audio route.

## Deliver the requested contract

Always include **批次总览** — each supplied input, local file path when available, and `complete` / `partial` / `blocked` status. Then include only the requested modules:

1. **学习笔记** — summary, `[hh:mm:ss]` steps, commands/settings with evidence, decisive keyframes, risks, and a reproduction checklist.
2. **视频理解/筛片/粗剪** — event cards, representative frames, directly observed descriptions, evidence labels, review priority, and derived candidate paths when requested.
3. **精彩片段候选** — ranked intervals, the evidence for each ranking, and uncertainty; do not call an interval a confirmed highlight merely from model preference.
4. **互动/对话候选** — time ranges, raw transcript, visible interaction evidence, and the explicit identity boundary.
5. **候选片段导出** — derived-file paths, source interval, context padding, and a statement that originals remain unchanged.
6. **全景粗剪** — paired `360 master candidate` and `reframed candidate` paths, exact source interval, quality/export settings, recognized-person evidence, and dialogue/speaker-attribution boundary.

Example: for `D:\\Courses\\open-design.mp4`, inspect subtitle/audio streams first, then collect transcript, keyframes, OCR, and visual observations over the same timeline. Do not require `yt-dlp`; it is relevant only to URLs. If Faster-Whisper is absent, still use the other available evidence sources and disclose the missing audio evidence.

Read [references/runtime-setup.md](references/runtime-setup.md) only when a runtime component is missing or the user asks about installation, cost, or background audio capture.

Read [references/v2-pending-design.md](references/v2-pending-design.md) when a request involves unimplemented rough cutting, named-person recognition, speaker attribution, or raw `.insv` automation. Treat that document as a design and dependency record, not proof that a capability is available.
