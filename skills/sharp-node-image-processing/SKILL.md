---
name: sharp-node-image-processing
description: Use when Codex needs programmatic image processing in a Node.js project or service, including Buffer or Stream transforms, thumbnails, high-throughput resize, metadata inspection, format encoding, compositing, or image pipelines that must run inside JavaScript. Do not use for one-off local deterministic edits better served by ImageMagick, or for generative image changes.
---

# Sharp Node Image Processing

## Routing boundary

- Use Sharp for Node project code, services, worker pipelines, Buffer/Stream input, in-memory output, and high-throughput thumbnail or format processing.
- Keep one-off local crop, resize, composite, text, mask, or pixel-diff work on `$imagemagick-image-editing`.
- Keep generative or semantic edits on built-in `image_gen`. Keep explicit CLI image generation on the GPT Image Skill.
- Do not install `sharp-cli`; it is not the official `lovell/sharp` package and is unnecessary here.

## Dependency rule

- For code that will ship with a Node project, use the project's local `sharp` dependency. Do not make deployed code depend on this workstation's global package.
- If the project lacks `sharp`, ask before adding it to that project's `dependencies`.
- For ad-hoc agent processing only, use the globally installed package via `NODE_PATH=(npm root -g)` and a short `node -e` invocation. Do not leave a one-off `.js` script behind.

## Workflow

1. Inspect source image metadata with `sharp(input).metadata()` and inspect visually when the output depends on content.
2. Preserve source files unless the user explicitly requests an overwrite.
3. Decide resize fit, position, background, alpha, format, quality, and metadata behavior before processing.
4. Run the Sharp pipeline. Await `toFile`, `toBuffer`, or the Stream completion; do not assume calling a method has written output.
5. Reopen the output with Sharp, check format and dimensions, then use `view_image` for visual verification.

## Project usage

Use the local dependency in ESM code:

```js
import sharp from 'sharp';

await sharp(inputPath)
  .rotate()
  .resize({ width: 864, height: 1821, fit: 'cover', position: 'centre' })
  .webp({ quality: 90 })
  .toFile(outputPath);
```

Use `fit: 'contain'` with a deliberate `background` when the full image must remain visible. Use `fit: 'cover'` only when crop is acceptable. Use `.rotate()` to honor EXIF orientation.

## Ad-hoc global usage

In PowerShell, expose the global npm root only for the current command:

```powershell
$env:NODE_PATH = (npm root -g).Trim()
node -e 'const sharp=require("sharp"); (async()=>{ await sharp(process.argv[1]).resize(640,360,{fit:"cover"}).webp({quality:90}).toFile(process.argv[2]); })().catch(error=>{console.error(error);process.exit(1)});' "D:\input.png" "D:\output.webp"
```

For a non-trivial operation, use a project-local module or ask before creating a reusable script. Do not turn a simple transform into a persistent script file.

## Common operations

| Goal | Sharp pipeline |
|---|---|
| Read metadata | `await sharp(input).metadata()` |
| Resize and crop | `.resize({ width, height, fit: 'cover', position: 'centre' })` |
| Fit without crop | `.resize({ width, height, fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })` |
| Composite layer | `.composite([{ input: overlayPath, gravity: 'centre', opacity: 0.35 }])` |
| Convert format | `.webp({ quality: 90 })`, `.jpeg({ quality: 90 })`, or `.png()` |
| Buffer result | `.toBuffer()` |
| File result | `.toFile(outputPath)` |

## Verification and risks

- Verify output with `await sharp(output).metadata()`; then visually inspect when placement, compositing, or text matters.
- Do not promise a pixel-identical unchanged area from Sharp transforms without a separate pixel-diff check; use ImageMagick comparison when that is a requirement.
- Be deliberate about `.withMetadata()`: preserve metadata only when requested. Metadata can contain orientation, color profiles, and privacy-sensitive EXIF fields.
- Do not process unbounded or untrusted image inputs without setting an appropriate pixel limit or validating source dimensions in application code.
