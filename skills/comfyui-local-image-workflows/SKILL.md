---
name: comfyui-local-image-workflows
description: Use when local offline image generation needs reproducible seeds, ComfyUI workflow control, reference-image composition or style consistency, or batch-consistent AI-video keyframes. Do not use for ordinary one-off generation or conversational image edits.
---

# ComfyUI Local Image Workflows

Use the local ComfyUI server for repeatable FLUX work, not as the default image generator.

## Choose the route

| Need | Use |
|---|---|
| Ordinary text-to-image or conversational edit | Built-in `image_gen` |
| Fixed seed, local/offline generation, repeated shots | FLUX.1-dev FP8 checkpoint |
| Reference image affects composition, palette, or visual style | FLUX Redux |
| Preserve most of an image while regenerating a masked area | FLUX Fill; warn that it is slow |

Do not use Redux as a promise of exact character identity. Do not use FLUX.1-dev for commercial work; the installed model is for non-commercial use.

## Start and verify

Before submitting, check `http://127.0.0.1:8188/object_info`. If unavailable, check and start the existing current-user scheduled task `ComfyUI Local API`, then poll the endpoint until ready. That task is the agent-facing local-only API and starts without a visible console window. If the user asks to open or operate Comfy Desktop, start Desktop normally and visibly; do not hide its UI. Reuse an already listening API instead of starting a second backend, and do not change its port, loopback binding, task, or launcher unless the user explicitly requests it. Do not bypass antivirus or request an antivirus exclusion.

## Installed models

- Checkpoint: `flux1-dev-fp8.safetensors`
- Redux: `flux1-redux-dev.safetensors` plus `sigclip_vision_patch14_384.safetensors`
- Fill: `flux1-fill-dev.safetensors`

Use `CheckpointLoaderSimple` for the FP8 checkpoint. Its model, CLIP, and VAE outputs are the validated text-to-image entry point. Do not use the old split-model FLUX template or download its missing split components.

Use FLUX defaults unless task-specific evidence calls for another value: 20 steps, Euler, simple scheduler, CFG 1.0, Flux Guidance 3.5. Keep `ModelSamplingFlux` and `EmptyLatentImage` dimensions identical.

## Automatic submission

Use `scripts/submit_comfy_workflow.py`; it submits locally and returns JSON containing the output image path. Build its arguments with a temporary PowerShell argument array, then execute that temporary file through RTK so prompts with spaces remain one argument.

| Route | Command inputs |
|---|---|
| FLUX text-to-image | `--workflow t2i --prompt ...` |
| Redux reference image | `--workflow redux --prompt ... --reference <image>` |
| Fill final retouch | `--workflow fill --prompt ... --image <image> --mask <black-white mask>` |

Choose prompt, seed, dimensions, and steps from the request; use the defaults when unspecified. Do not ask the user to assemble nodes or run commands. Stage reference, source, and mask files automatically; return the generated image in the final response.

## Cost and execution

All listed workflows run locally and need no API key or per-image payment after models are downloaded. Save output and record seed, prompt, model, dimensions, and key sampler settings when reproducibility matters. FLUX Fill is only for small amounts of final retouching or when the user explicitly requests it; say that a 512x512 test took about 370 seconds on this machine.
