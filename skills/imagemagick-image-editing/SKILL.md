---
name: imagemagick-image-editing
description: Use when Codex needs deterministic local image editing on Windows, including crop, resize, canvas fitting, compositing, overlays, masks, transparency, text, format conversion, batch processing, metadata inspection, or pixel-difference validation. Prefer ImageMagick CLI over writing one-off System.Drawing, Pillow, PowerShell, Python, or Node image-processing scripts when a clear ImageMagick command can perform the work.
---

# ImageMagick Image Editing

## Core rule

Use direct ImageMagick commands for deterministic local edits. Do not create a one-off wrapper script when the operation can be expressed clearly as one ImageMagick pipeline or a short PowerShell argument array.

## Routing boundary

- Use this skill for pixel-level operations whose desired result is fully specified: geometry, canvas, layers, alpha, masks, text, formats, metadata, batch transforms, and comparisons.
- Use built-in `image_gen` for generative or semantic changes such as replacing a person, inventing missing content, changing style, or regenerating an object.
- Use the existing GPT Image skill when the user explicitly asks to generate or edit through a CLI image model.
- If ImageMagick cannot express the operation clearly and reliably, explain why before writing a small reusable script. Do not silently fall back to System.Drawing, Pillow, or Node canvas.

## Workflow

1. Inspect every relevant source image with `view_image` when the operation depends on visual content. Use `magick identify` for dimensions, format, channels, orientation, and profiles.
2. Resolve `magick.exe` with `Get-Command magick.exe`. If the current process has stale PATH state after installation, locate it under `C:\Program Files\ImageMagick-*` and invoke the absolute path.
3. Decide the exact geometry, gravity, background, alpha, color-profile, and output-format behavior before running the edit.
4. Preserve source files by default. Write a new output path unless the user explicitly requests an overwrite.
5. Invoke the executable with a PowerShell argument array. Capture `$LASTEXITCODE` immediately and read warnings as well as errors.
6. Verify metadata with `magick identify`, then inspect the output with `view_image`.
7. For strict invariants such as "all pixels outside this rectangle must remain unchanged," verify with a mask plus `magick compare` or an equivalent pixel count.

## Safe Windows invocation

Use one array item per native argument:

```powershell
$magick = (Get-Command magick.exe -ErrorAction Stop).Source
$nativeArgs = @(
    'input.png'
    '-auto-orient'
    '-resize', '864x1821^'
    '-gravity', 'center'
    '-extent', '864x1821'
    'output.png'
)
& $magick @nativeArgs
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) { throw "ImageMagick failed with exit code $exitCode" }
```

- Use absolute paths for inputs and outputs.
- Use forward slashes in font paths passed to ImageMagick, for example `C:/Windows/Fonts/msyh.ttc`. Backslashes can be consumed as escapes by ImageMagick's font parser.
- Specify a Chinese-capable font explicitly for Chinese text.
- Do not use `Invoke-Expression`, a single deeply quoted command string, or the legacy `convert.exe` command.

## Common operations

| Goal | ImageMagick argument pattern |
|---|---|
| Inspect | `identify -format %f\|%m\|%wx%h\|%[channels] input.png` |
| Fill and crop | `input.png -auto-orient -resize 864x1821^ -gravity center -extent 864x1821 output.png` |
| Fit without crop | `input.png -auto-orient -resize 864x1821 -gravity center -background none -extent 864x1821 output.png` |
| Crop rectangle | `input.png -crop 460x96+730+93 +repage output.png` |
| Composite overlay | `background.png overlay.png -gravity center -geometry +0+30 -composite output.png` |
| Set layer opacity | `overlay.png -alpha set -channel A -evaluate multiply 0.35 +channel output.png` |
| Add Chinese text | `input.png -font C:/Windows/Fonts/msyh.ttc -pointsize 48 -fill white -gravity north -annotate +0+40 标题 output.png` |
| Convert format | `input.webp -quality 92 output.jpg` |
| Exact comparison | `compare -metric AE expected.png actual.png diff.png` |

For a batch, loop over source files in PowerShell and invoke the same direct argument array for each file. Do not generate a `.ps1`, `.py`, or `.js` file merely to hold the loop.

## Verification details

- Treat `identify` as metadata verification, not visual verification.
- Use `view_image` to check crop placement, text rendering, layer ordering, transparency, and unintended clipping.
- `magick compare` normally returns `0` for equality, `1` for a valid difference, and a higher value for an execution error. Interpret the metric and exit code together.
- Preserve profiles and orientation unless the requested output requires normalization. Use `-auto-orient` deliberately, because it changes pixel layout.
- For an allowed-change region, mask that region out and compare the remaining pixels instead of assuming a successful composite preserved them.

## Common mistakes

- Do not confuse `864x1821` fit with `864x1821^` fill-and-crop.
- Do not rely on a default font for Chinese.
- Do not hide warnings emitted on stderr when the exit code is zero.
- Do not overwrite the only copy of a source image.
- Do not claim that only a requested region changed without a masked pixel comparison.
