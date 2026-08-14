# Health and paths

Use this reference when a route needs a new or revalidated local/software/credential health state. A new state means the first attempt in this conversation for that route/service and relevant model/node/provider, not the first ordinary media request globally. Reuse a successful check within the active conversation instead of repeating it before every ordinary task. Recheck after a process/API restart, a failed call, a relevant model/node/provider change, or an uncertain external-state change. Validate only newly introduced assets or newly broadened authorization scope; reuse confirmation for the same assets and scope within the conversation. Select a newly requested or different target model separately, while rechecking its availability only when the health-state rule requires it. Status means: `ready` = required checks pass for this action; `partial` = some chain parts work but an input/workflow/production proof is absent; `missing` = a required component is absent; `blocked` = policy, authorization, or model-selection prevents action.

| Component | Verified root or endpoint | Minimum check |
| --- | --- | --- |
| ComfyUI API | `http://127.0.0.1:8188/object_info`; shared root `D:\Comfy-Desktop\ComfyUI-Shared` | Request `object_info`; confirm the required node and model dropdown include the exact model before submission. |
| Comfy input/output | input `D:\Comfy-Desktop\ComfyUI-Shared\input`; output root `D:\Video\Comfyui` | Confirm the active backend uses the shared input and new output root. Native jobs use `Image\<job>` or `Video\<job>`. |
| MiniMax H3 (GGUF) | `http://127.0.0.1:8188/object_info` | Confirm `MiniMaxH3ImageToVideo` exists; `UnetLoaderGGUF` lists `MiniMax-H3-FL2VA-Q4_K_M.gguf`; `CLIPLoaderGGUF` lists `qwen3vl_32b_minimax_h3-Q4_K_M.gguf` with type `minimax`; `VAELoader` lists `minimax_h3_video_vae_fp16.safetensors` and `minimax_h3_audio_vae_fp32.safetensors`. |
| rembg | `D:\AI\rembg` | Run its dedicated venv entry and confirm `CUDAExecutionProvider` is first; confirm the selected ONNX model exists. |
| Standalone image editing/cutout | outputs `D:\MediaStudio\Image` | Create one safe `<job>` directory; project assets and native ComfyUI images use their owning roots instead. |
| Video learning | tools `D:\CodexVideoLearning`; standalone outputs `D:\MediaStudio\VideoLearnings` | Confirm `VIDEO_LEARNING_ROOT` and `VIDEO_LEARNINGS_ROOT`, then run its runtime check. |
| Voice | runtime `D:\AI\Voice`; standalone outputs `D:\MediaStudio\Voice` | Use each product's venv/entry rather than global Python. |
| MuseTalk | runtime `D:\AI\Video\MuseTalk`; standalone outputs `D:\MediaStudio\MuseTalk` | Check its declared CLI and available GPU before processing. |
| Whole-person reconstruction | PuLID, Union ControlNet/depth or pose control, Wan I2V, and authorized target references | Confirm exact live node/model dropdowns and a saved Canvas/API pair for the shot. This is not evidence of a dedicated ReActor/SimSwap/FaceFusion face-swap chain. |

For agent-driven ComfyUI API work, use the existing hidden local API task. For user-operated canvas work, launch Comfy Desktop visibly. Reuse a healthy service; do not start a second backend on port 8188.

## Credential and connection checks

Check only existence and reachability, never values. Kitool GPT Image has a private local configuration; XYQ uses a user/process environment variable; Hugging Face restricted downloads use the Windows credential helper; HeyGen uses its connected MCP. OpenAI API availability is independent of built-in Codex image generation. Treat missing provider configuration, exhausted quota, or unknown model selector as `missing` or `blocked`.

## Comfy model gate

Before a route, verify the relevant names appear in the actual API dropdowns: FLUX checkpoint/CLIP/VAE for FLUX; PuLID model and Union ControlNet for identity plus pose; Wan UNET, UMT5 text encoder, and Wan VAE for Wan. The shared library contains verified components, but a new Canvas/API JSON pair and material-specific output remain separate acceptance work. MiniMax H3 follows the same gate: verify its GGUF unet/text encoder and both VAEs in the live dropdowns before submission.

For a request to replace an entire person while retaining source staging, use the authorized-reference reconstruction route: PuLID for identity, Union ControlNet/depth or pose for visible structure, and per-shot Wan I2V for motion. Do not describe it as, or substitute it for, a dedicated face-only swap. ReActor, SimSwap, and FaceFusion are currently `missing` on this workstation unless a later verified install and workflow record says otherwise.

Never copy models, outputs, private inputs, credential files, or caches into a repository merely to make a check pass.

## Face scan model-root gate

For `screen_video_batch.py` or `scan_known_faces.py`, pass `D:\CodexVideoLearning\models\face-recognition` as `--model-root`. `create_face_analysis()` appends `models\antelopev2` internally. Passing the nested `...\face-recognition\models` path makes InsightFace treat its existing model as absent and can trigger an unintended duplicate download. Before any face scan, confirm the expected `models\antelopev2` directory exists and that its CUDA provider preflight succeeds.
