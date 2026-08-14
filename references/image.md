# Image routing

Select one primary route. Preserve source files and write a new output unless the user explicitly approves replacing a named derived file.

| Need | Route | Gate |
| --- | --- | --- |
| Normal semantic generation, replacement, inpainting, or restyling | built-in `image_gen` | Default; use it unless deterministic local control is required. |
| Explicit CLI GPT Image request | `gpt-image` | Use Kitool GPT-Image-2; default 2K unless the user requests 4K. Confirm private configuration exists. |
| Crop, resize, canvas fit, compositing, mask, alpha, text, format conversion, batch, or pixel comparison | `imagemagick-image-editing` | Prefer ImageMagick over a throwaway image script. Verify output with `identify` and visual inspection when relevant. |
| Node project Buffer/Stream or service image pipeline | `sharp-node-image-processing` | First obtain approval to add project-local `sharp`; do not make a saved project depend on a global package. |
| Person/character transparent PNG | `rembg-background-removal` + `u2net_human_seg` | Check CUDA provider and model. Use alpha matting only for hair, fur, or semitransparent edges. |
| Non-person object transparent PNG | `rembg-background-removal` + `isnet-general-use` | Check CUDA provider and model. |
| Offline/fixed-seed/reproducible/batch-consistent keyframe | `comfyui-local-image-workflows` | Check live API nodes and model dropdowns first. |
| Identity plus specified pose/composition | ComfyUI PuLID-Flux + FLUX Union ControlNet | Need authorized identity images, pose/composition input, and a saved Canvas/API pair. Redux and Fill are not substitutes. |

For project work, save the final image under the project's existing asset contract. For a standalone native ComfyUI image job, use `D:\Video\Comfyui\Image\<job>`. For a standalone GPT Image job, including GPT Image semantic edits, download the generated image and record to `D:\MediaStudio\GPT-Imag\<job>`; a remote URL alone is not a completed local delivery. For standalone ImageMagick, rembg, or Sharp image-editing work, use `D:\MediaStudio\Image\<job>`. Jianying last-frame keeps its task-selected path unless a project contract owns it.

FLUX.1-dev is non-commercial. FLUX Fill is for limited final masked refinement and may be slow. A fixed-seed FLUX text-to-image smoke test proves only the tested baseline; do not promote it to identity or video-quality proof.
