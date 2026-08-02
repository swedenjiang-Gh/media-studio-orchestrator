---
name: local-voice-studio
description: Use when a user asks to synthesize speech, clone an authorized voice, create local narration, convert an existing recording to another authorized voice with RVC, use VoxCPM2 or GPT-SoVITS, or generate an authorized MuseTalk lip sync/video dubbing result. Trigger for RVC, voice conversion, speech-to-speech, existing-recording voice change, 已有录音换音色, MuseTalk, lip sync, video dubbing, 对口型, 视频配音, or 嘴型同步.
---

# Local Voice Studio

Use the installed local engines. Before a voice-cloning job, confirm the reference voice is the user's or has explicit authorization. Keep reference audio and output under `D:\AI\Voice` unless the user specifies another local path.

## Choose an engine

| Need | Engine |
|---|---|
| New multilingual voice, text-controlled style, or one-off authorized clone | VoxCPM2 |
| Train a character voice from a longer dataset or use the full GUI workflow | GPT-SoVITS |
| Keep an existing recording's spoken content and timing while changing it to an authorized target timbre | RVC |
| 已有视频/人物图 + 音频，生成对口型视频 | MuseTalk |

## VoxCPM2

Use `D:\AI\Voice\VoxCPM2\generate.py` with its dedicated CUDA runtime.

```powershell
& 'D:\AI\Voice\VoxCPM2\.venv\Scripts\python.exe' 'D:\AI\Voice\VoxCPM2\generate.py' `
  --text '你好，这是本地配音。' `
  --output 'D:\AI\Voice\outputs\voxcpm2.wav'
```

Add `--reference-audio <authorized wav>` for controllable timbre cloning. Add both `--reference-audio` and `--reference-text <exact transcript>` for maximum-similarity cloning. Do not silently overwrite an existing output path.

## GPT-SoVITS

The installed root is `D:\AI\Voice\GPT-SoVITS\GPT-SoVITS-v3lora-20250228`.

- Start the WebUI with `go-webui.bat` from that root, then use its displayed local URL.
- Use the WebUI for dataset preparation, training, and selecting trained GPT/SoVITS weights.
- The optional local API is `runtime\python.exe api_v2.py -a 127.0.0.1 -p 9880`, run with that root as the working directory.

Do not start public sharing or bind to a non-loopback address unless the user explicitly asks.

## RVC

Use RVC only for speech-to-speech conversion: it changes the timbre of an existing recording. Do not substitute it for text-to-speech; use VoxCPM2 or GPT-SoVITS when the user starts from text.

The installed root is `D:\AI\Voice\RVC`. Its CUDA environment and RVC base assets are already installed.

- Confirm that both the source recording and the target voice model are the user's or explicitly authorized before conversion or training.
- Put an authorized target model at `assets\weights\<name>.pth`; put its optional matching retrieval index at `assets\indices\<name>.index`.
- Start the local-only WebUI from the RVC root with `& '.\.venv\Scripts\python.exe' '.\webui.py' '--noautoopen' '--port' '7865'`, then open `http://127.0.0.1:7865`.
- In the inference tab, select the target `.pth`, optionally select its matching `.index`, upload the source recording, set pitch shift only when required, and export a new output path. Do not overwrite an existing audio file without the user's approval.
- Use the training tabs only with a clean, consistently authorized target-voice dataset. A trained `.pth` without a matching `.index` can run, but the index can improve timbre retrieval.

## MuseTalk

Use MuseTalk v1.5 for an existing video or person image plus driving audio. Before running it, confirm that both the visible person's likeness and the driving audio are the user's or explicitly authorized.

The installed root is `D:\AI\Video\MuseTalk`. Use the CLI wrapper rather than the WebUI:

```powershell
& 'D:\AI\Video\MuseTalk\.venv\Scripts\python.exe' 'D:\AI\Video\MuseTalk\run-lipsync.py' --video 'D:\AI\Video\input.mp4' --audio 'D:\AI\Voice\input.wav' --output-dir 'D:\AI\Video\outputs' --output-name 'result.mp4'
```

- Pass absolute existing paths. Omit `--output-name` to use the generated name. The target `.mp4` must not already exist; the wrapper will refuse to overwrite it.
- Each job keeps its YAML and isolated workspace under `<output-dir>\.musetalk-jobs`; it does not put upstream temporary cleanup beside source media.
- MuseTalk v1.5 uses GPU 0 with fp16 and a fixed `bbox_shift` of zero. Do not promise that CLI exposes mouth-region shifting.
- Use `http://127.0.0.1:7860` only as the fallback for mouth-region troubleshooting or visual diagnostics; normal Codex jobs should call the CLI.
