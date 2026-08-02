---
name: rembg-background-removal
description: Use when removing a photo or asset background, cutting out a person or object, preparing a transparent PNG for image-to-image or video workflows, or when the user asks for local AI segmentation, hair-edge extraction, or batch background removal on Windows.
---

# Rembg Background Removal

Use the installed CUDA rembg environment for semantic foreground separation. Do not use it for generative edits; use ImageMagick for deterministic non-semantic edits and image_gen when a removed area must be invented.

Run the fixed wrapper; do not write a one-off image-processing script:

```powershell
& 'D:\AI\rembg\venv\Scripts\python.exe' 'D:\AI\rembg\remove-background.py' <input> <output.png> --model u2net_human_seg
```

- Use `u2net_human_seg` for a person or character.
- Use `isnet-general-use` for a non-human foreground object.
- Add `--alpha-matting` only when hair, fine fur, or translucent edges need refinement; it is slower. It is not automatically cleaner: inspect the result for background haze or halos before using it as a final hair-edge asset.
- Keep output as PNG. Verify it is RGBA before handing it to image-to-image or video tools.
- The wrapper refuses CPU fallback. Models live in `D:\AI\rembg\models`.
