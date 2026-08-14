# Video routing

## Download, learning, subtitles, and clips

For an authorized URL, use `download-videos`; do not bypass DRM, paywalls, or access controls. Then use `video-learning` for media probing and the evidence needed for the requested learning result. The default delivery is learning notes and a summary; do not automatically screen clips, recognize faces, create a new SRT, or translate non-Chinese dialogue. Keep the original embedded/external subtitle track and source timecodes.

Keep downloaded sources and subtitle sidecars under `D:\MediaStudio\VideoDownloads\<platform>`. A standalone learning job owns `D:\MediaStudio\VideoLearnings\<job>`; a project-owned learning result follows the project directory instead. Do not duplicate the downloaded source into either destination.

Enable an extra delivery stage only when the user explicitly requests it: `外挂字幕`/`字幕` creates a new SRT; `双语字幕`/`翻译` creates source-plus-Simplified-Chinese SRT; `筛片`/`粗剪`/`精彩片段`/`有对话片段` creates review candidates; a family-video request to find a named person or require their complete visibility enables the reference-library face review route. A family-video request for only highlights or dialogue does not enable face scanning.

## Subtitle status

The implemented screening-delivery route is `scripts/external_subtitles.py` plus `scripts/screen_video_batch.py`. It writes an external UTF-8 **SRT** beside the source and each master/reframed candidate, preserves raw ASR text and timecodes, and rebases the derived-candidate timecodes. For non-Chinese ASR it adds a second Simplified-Chinese line only after numbered-result validation; malformed, incomplete, echoed, timed-out, or missing translation remains explicit `partial` rather than fabricated.

On this machine, that implementation was merged as `1ced889`; the auto-discovered primary checkout is now synchronized through `3e23b08`. Its 93 tests and a prior real-video delivery are verified. Run the normal runtime/material checks before each new job, but do not call the implementation absent.

For requested bilingual subtitles, prefer an accessible platform Chinese VTT as translation evidence. `screen_video_batch.py` auto-discovers a same-stem `.zh-CN.vtt` sidecar, preserves raw ASR separately, then assembles it into complete sentence or utterance units before writing an external bilingual SRT. Do not use a fixed count of ASR fragments as a translation batch boundary. Use midpoint alignment first; if no midpoint falls inside the unit, accept only the single greatest-overlap platform cue when it covers at least 20% of the unit. For uncovered units, send the complete unit plus neighbouring context to the local translator and require complete numbered output. The `rKgtm81yi94` source passed this semantic-unit SRT route with a retained manual wording/timing review gate.

This route delivers external SRT. VTT output and FFmpeg subtitle attachment/burning are not part of its verified implementation. Never replace original captions with a translation.

For known-person recognition, use the read-only reference index and calibrated same-model embeddings. Emit review candidates and metrics, not an unsupported name assertion. For Insta360, keep the `.insv` original and the 2:1 equirectangular master; selected-frame extraction and stitched delivery are separate checks. Do not scan whether a face remains in-frame by default: when requested, screen only highlights and dialogue. Use Insta360 Studio Deep Track for a stable subject-following reframed view; the local SDK route may be used for this only after its continuous-tracking API is verified.

## Video prompt reverse engineering

For an authorized local or public-reference video, use `video-learning` first for media facts and an event-driven entry/peak/exit evidence manifest, then route the four separate evidence streams through `video-prompt-reverse`: SkyCaptioner structure, controller/general-VLM observations, ASR/OCR, and explicit human context. Deliver the validated JSON plus derived Markdown with T2V/I2V reconstruction prompts, an enhanced prompt, three single-variable variants, five-role review, separated negative categories, explicit uncertainties, and a source-closed one-row-per-atom attribution ledger. A model load, structural caption, unvalidated draft, or incomplete attribution ledger is only `partial`.

Use four bounded local 32B stages and one deterministic controller pass. The controller must downgrade unprovable source claims instead of fabricating closure, repair copied variant sections into declared single-variable changes, bind copied I2V drafts to an approved task-local first frame when present, and clean implementation-oriented negatives. Evidence extraction and prompt fusion do not need ComfyUI; do not start it for reverse analysis, and do not overlap 32B fusion with H3/Wan generation.

Prompt reverse engineering does not authorize generation. After delivery, offer MiniMax H3, Wan/local, Seedance/cloud, another engine, or no generation as explicit choices. If the user has already authorized a named acceptance generation in the same task, reuse the stored ComfyUI Canvas/API pair and record prompt correctness separately from rendered similarity, audio, and production quality.

A standalone reverse job owns `D:\MediaStudio\VideoPromptReverse\<job>`. If an authorized comparison render is created through ComfyUI, keep the canonical render under that reverse job; ComfyUI is the executor, not the output owner. Project-owned reverse results follow the project directory.

## Local generation

### Depth-map video

When the user asks for “深度黑白视频”, a depth map, depth-conditioned dance replacement, or a grayscale structural guide, route the depth stage to `video-depth-map`. This is not a color-grade operation. The local route is `partial` until a depth-estimation model or ComfyUI depth node is visible and a real time-aligned output has been rendered. `faster_whisper` and Tesseract support transcription/OCR only and do not provide depth estimation. Do not start ComfyUI for a learning-only explanation; use it only for an explicitly requested generation workflow.

For a standalone depth task, use ComfyUI only as the execution engine and deliver the grayscale video, optional inferno preview, metadata, and review evidence under `D:\MediaStudio\VideoDepthMaps\<job>`. Project-owned depth results follow the project directory. Native standalone Wan/H3 generation that is not owned by another specialist uses `D:\Video\Comfyui\Video\<job>`.

Local video generation is a first-class route equal to the cloud, not merely a preview: Wan 2.2 T2V 14B (text to video, ≈2.10 min at 832×480/3 s), Wan 2.2 I2V 14B (≈1.50 min), and MiniMax H3 (T2V/I2V with native AAC 32 kHz audio, ≈2.0–2.3 min). When the user asks to generate a video, present both routes (local vs cloud) and let the user choose before spending quota or compute; do not default to cloud with local treated only as a reminder. Choose local for free generation, fixed-seed reproducibility, controlled outputs, privacy, and batch-consistent shots; choose cloud when the local chain cannot meet the requested model/quality/duration/audio or the user explicitly picks it.


Use `comfyui-video-workflow-author` for FLUX keyframes, PuLID/Union ControlNet, Wan, and MiniMax H3 (GGUF). Before Wan I2V/T2V submission, verify Wan model components in the live API and store a matching Canvas JSON, API JSON, and explanation. A verified Wan 1.3B file is not a completed text-to-video workflow; an I2V request also needs an approved first frame, target duration/fps/resolution, and action brief. Wan 2.2 T2V 14B FP8 + LightX2V v1.1 4-step LoRA is installed and chain-verified on 2026-08-06 (832×480/3s ≈ 2.10 min, silent output); Wan 2.2 I2V 14B FP8 remains the verified I2V path (≈ 1.50 min at the same spec). Per-shot inputs, prompts, and outputs still require acceptance. MiniMax H3 reuses the stored `minimax-h3-t2v` / `minimax-h3-i2v` Canvas/API pairs; its T2V smoke test passed on 2026-08-06 with H.264 24fps video and AAC 32kHz stereo audio.

## Cloud generation

Before a paid cloud submission, offer an optional local dry-run when the shot is previewable locally — Wan 2.2 T2V 14B (text to video, 832×480/3 s ≈ 2.10 min), MiniMax H3 (T2V/I2V with native AAC 32 kHz audio, ≈ 2.0–2.3 min), Wan 2.2 I2V 14B (≈ 1.50 min), and Wan2ReferenceVideoApi / MiniMaxH3ReferenceToVideo for reference consistency. This is a reminder, not a gate: present the choice and let the user decide per submission (local preview now, or submit to the cloud directly). The local preview does not replace the context-submission package, the explicit model-selection gate, or per-shot authorization.


Use `xyq-skill`, `xyq-short-drama-skill`, HeyGen, or another authorized entry only after writing/updating the project `视频生成任务上下文提交包.md`. It must state story, characters, style, shot order, action, model requirement, prohibitions, and asset order. If a named model such as Seedance 2.0 mini cannot be explicitly selected or reliably constrained by that entry, return `blocked` and do not submit. Check authorization, quota, asset order, and output-download rules before the request.
