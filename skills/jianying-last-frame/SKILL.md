---
name: jianying-last-frame
description: Export or capture the last frame from a specified Jianying/CapCut draft or from a video file. Use when the user asks to get, export, extract, save, or inspect the final frame/last frame of a 剪映草稿, Jianying draft, CapCut project, mp4/mov/m4v video, or a named draft such as "riding-system-awakening".
---

# Jianying Last Frame

## Goal

Produce a local image file for the final visible frame of a specified Jianying draft or video. Prefer source-quality extraction from the underlying video over screen screenshots.

## Safety Rules

- Do not modify draft files unless the user explicitly asks.
- Do not delete draft folders, temporary folders, logs, or media.
- Avoid `gen_video` for last-frame tasks unless the user explicitly allows it and you have inspected the local implementation for cleanup/export side effects.
- If using CapCut Mate on Windows, first check whether Jianying is running and whether the target draft is open before doing UI work.
- If the draft has multiple visual layers, text, stickers, filters, overlays, or effects active at the end, source-video extraction may not equal the composited final frame. In that case, export/render safely or explain the limitation before using a screenshot fallback.

## Decision Flow

1. If the user provides a video file path, run `scripts/extract_last_frame.py` directly.
2. If the user provides a draft folder path, inspect it without writing:
   - Old plaintext drafts: parse `draft_content.json` and identify the visible video segment covering the final timestamp.
   - New Jianying drafts may store `draft_content.json` as base64/binary encrypted content. Do not try to edit or decode by guessing. Use the Jianying UI and visible timeline/media names to identify the source video.
3. If the user provides only a draft name, locate it in common draft roots:
   - `E:\剪映\JianyingPro Drafts`
   - `%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft`
   - project-specific paths mentioned by local instructions
4. Open or inspect the draft in Jianying only as needed. For a simple draft with one video track, identify the source media name in the timeline or media bin, search project roots for that exact filename, and verify duration/resolution against the draft UI.
5. Extract the frame using the script and write to a clear output folder, such as:
   - `<project>\exports\<draft-name>-last-frame\<draft-name>-last-frame.png`
6. Verify the output:
   - file exists
   - dimensions are correct
   - image visually matches the final frame
   - report source video, output path, frame count, fps, duration when available

## Script Usage

Prefer a full `ffmpeg`/`ffprobe` build on PATH, or pass explicit paths with `--ffmpeg` and `--ffprobe`. The script automatically falls back to `imageio-ffmpeg` when `ffmpeg` is unavailable and `--backend auto` is used.

```powershell
python "C:\Users\j\.codex\skills\jianying-last-frame\scripts\extract_last_frame.py" `
  --video "E:\path\to\input.mp4" `
  --output "E:\path\to\last-frame.png"
```

Batch folder mode:

```powershell
python "C:\Users\j\.codex\skills\jianying-last-frame\scripts\extract_last_frame.py" `
  --input-dir "E:\path\to\videos" `
  --output-dir "E:\path\to\videos\last-frames"
```

When a full FFmpeg build is installed outside PATH:

```powershell
python "C:\Users\j\.codex\skills\jianying-last-frame\scripts\extract_last_frame.py" `
  --video "E:\path\to\input.mp4" `
  --output "E:\path\to\last-frame.png" `
  --ffmpeg "D:\tools\ffmpeg\bin\ffmpeg.exe" `
  --ffprobe "D:\tools\ffmpeg\bin\ffprobe.exe"
```

The script prints JSON metadata. Treat a successful image write plus visual inspection as the completion gate.

## Jianying Draft Notes

- CapCut Mate's `gen_video` workflow is for downloaded API drafts and can enqueue cleanup, upload output, or kill Jianying on failure depending on the local code. Inspect before use.
- Jianying 10.x draft files may be encrypted or packed even when named `.json`; do not assume `Get-Content draft_content.json` is valid JSON.
- `draft_cover.jpg` is useful evidence but is not automatically the final frame.
- If Computer Use screenshots fail, `pyautogui.screenshot()` can still document the current visible UI. Screen capture is a fallback, not source-quality extraction.
