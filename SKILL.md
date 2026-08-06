---
name: media-studio-orchestrator
description: Use as the required first entry point when a request involves local or cloud image generation/editing, background removal, ComfyUI/FLUX/Wan workflows, video download/analysis/subtitles/translation, video recognition/clipping, narration/voice conversion, lip sync, or multiple media capabilities. It selects and coordinates specialist Skills without replacing their execution rules.
---

# Media Studio Orchestrator

Route one media request to the smallest verified execution chain. This Skill coordinates existing specialist Skills, CLIs, APIs, and Desktop software; it does not replace or reimplement them.

## Entry-point ownership

For any image, video, or audio request, enter through this Skill before invoking a specialist Skill. A specialist may execute the selected step, but it must not bypass this Skill's health check, consent gate, route selection, or acceptance record. If multiple matching Skills are available, keep this Skill as the coordinator and name the selected specialist chain.

## Consistency ownership

Treat this Skill as the routing and acceptance index, not as a replacement for a specialist's executable rule. Keep one source of truth for each rule:

1. Put executable details—commands, API contracts, model/path dependencies, defaults, consent/safety gates, and quality procedures—in the relevant specialist Skill and its references.
2. Put cross-route selection, machine-wide state, and acceptance status here. Update `references/acceptance.md` only when the evidence status changes.
3. Update both only when the same fact is intentionally summarized in both places. Then read them together and remove any contradiction; do not duplicate long specialist procedures here.
4. Before reporting a change complete, check which source owns the changed fact, validate every changed Skill folder with `quick_validate.py`, and report whether a counterpart update was required or deliberately unnecessary.

Never leave the coordinator and a specialist with different rules for the same situation. A child-Skill-only update is correct when it changes only that child's operational detail; a coordinator-only update is correct when it changes only routing or acceptance evidence.

## Local workstation inventory

Read `local-machine/local-media-inventory.md` and `local-machine/storage-and-credentials.md` only when a request needs the current local capability/software inventory, capacity, paths, or credential-status notes. Do not read them for an ordinary media task that only needs its specialist Skill and minimum health check. This directory is deliberately Git-ignored: never commit it, copy its private values into a public artifact, or treat it as portable configuration.

Refresh both files on a material machine change (model added or removed, software installed or uninstalled, credential configuration changed) and at least monthly. Refresh means: recount the directory capacities with a recursive file-size sum, verify key model paths and sizes, sync capability status with `references/acceptance.md`, and record credential existence only, never values. After a refresh, if any tracked file changed, validate the Skill folder with `quick_validate.py` before reporting complete.

## Required order

1. Classify the requested outcome and whether it is local, cloud, deterministic, or generative.
2. Read only the relevant reference below.
3. If a dependent chain has no current verified health state—its first attempt in this conversation for that route/service and relevant model/node/provider—run the minimum dependency check in `references/health-and-paths.md`. Reuse a healthy state within the conversation; recheck after a process/API restart, a failed call, a relevant model/node/provider change, or an uncertain external-state change.
4. Return one state: `ready`, `partial`, `missing`, or `blocked`.
5. Enforce consent, model-selection, and project-context gates; then select the execution route.
6. Preserve source assets and record the output path, parameters, executor, and validation boundary.

| Request | Read | Default route |
| --- | --- | --- |
| Generate, edit, cut out, compositing, reproducible keyframes | `references/image.md` | image_gen, GPT Image CLI, ImageMagick, Sharp, rembg, or ComfyUI |
| Download, understand, subtitle, translate, recognize, clip, or generate video | `references/video.md` | download-videos, video-learning, ComfyUI Wan, or authorized cloud entry |
| Narrate, clone/convert an authorized voice, or lip sync | `references/audio.md` | VoxCPM2, GPT-SoVITS, RVC, or MuseTalk |
| A chain has an unavailable service, model, CUDA dependency, port, path, or credential | `references/health-and-paths.md` | verify first; do not guess |
| User supplies test assets or asks whether production quality is proven | `references/acceptance.md` | follow the applicable acceptance gate |

## Route boundaries

- Ordinary semantic image generation/editing uses built-in `image_gen`; an explicit CLI request uses `gpt-image`.
- Pixel-exact edits use `imagemagick-image-editing`. Node Buffer/Stream work uses `sharp-node-image-processing` only after approval to add a project-local dependency.
- Semantic cutouts use `rembg-background-removal`. Fixed seed, offline, batch-consistent, or identity-plus-pose keyframes use the appropriate ComfyUI specialist Skill.
- Ordinary video learning defaults to evidence-based understanding and a summary only. Screening/rough cuts, face recognition, new external subtitles, and non-Chinese translation are opt-in stages that require an explicit user request. Preserve original subtitles and timecodes. Do not claim a new SRT/VTT, subtitle attachment, or burned delivery until the actual writer/FFmpeg entry and a video smoke record are present.
- Any cloud video submission requires a current `视频生成任务上下文提交包.md`. A requested model is `blocked` when the chosen entry cannot explicitly select or reliably constrain it.
- Voice/portrait work requires authorization for every supplied voice, recording, image, and video. Never silently train a voice model or overwrite source media.

## Do not assume

- A model file, node, installed package, or configured credential proves a working production chain.
- A queued cloud request, HTTP 200, or generated output proves identity, pose, lip-sync, translation, speaker attribution, or visual quality.
- A person recording alone is enough for long-form GPT-SoVITS/RVC training; use the material gate in `references/acceptance.md`.
- The hidden ComfyUI API task and a manually opened visible Comfy Desktop may start competing servers on port 8188.
- Download permission, platform login, model availability, or requested cloud-model selection without checking.

## Compact output contract

Report: selected route, state, checks performed, required inputs or authorization, submitted/not submitted, output location when created, and the remaining validation boundary. Do not expose credential values, cookies, tokens, or private asset paths in a public artifact.

## Acceptance presentation

When a task creates or validates a media artifact, make the evidence visible in the conversation instead of reporting only a path, log, or `pass` label:

- For image generation, editing, or cutouts, display the source and result together when comparison matters; for identity or structure checks, use a labeled side-by-side view.
- For video, provide a playable local output when available and show representative timestamped source/output frames for the claimed property. Do not substitute a workflow graph or queue record for the result.
- For audio, provide a playable sample or a precise statement that no authorized playback artifact exists.
- State separately: what passed, what visibly failed or remains uncertain, and the exact decision or material still needed from the user. A representative preview does not replace the saved output path or full-quality file.

If inline playback or preview is unavailable, say why and provide the exact local artifact path. Do not silently omit the evidence merely because the file was generated successfully.