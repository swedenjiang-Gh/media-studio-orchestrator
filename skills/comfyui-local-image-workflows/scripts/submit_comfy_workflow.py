import argparse
import json
import shutil
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SERVER = "http://127.0.0.1:8188"
INPUT_DIR = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
OUTPUT_DIR = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")
CHECKPOINT = "flux1-dev-fp8.safetensors"


def api_json(url, body=None):
    request = Request(url, method="POST" if body is not None else "GET")
    if body is not None:
        request.data = json.dumps(body).encode("utf-8")
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"ComfyUI API is unavailable: {error}") from error


def stage_input(path_text):
    source = Path(path_text).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Input file was not found: {source}")
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    name = f"codex-{uuid.uuid4().hex[:8]}-{source.name}"
    shutil.copy2(source, INPUT_DIR / name)
    return name


def common_nodes(args):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": args.prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": args.negative, "clip": ["1", 1]}},
        "5": {"class_type": "ModelSamplingFlux", "inputs": {"model": ["1", 0], "max_shift": 1.15, "base_shift": 0.5, "width": args.width, "height": args.height}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": args.width, "height": args.height, "batch_size": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": f"codex_flux_{args.workflow}"}},
    }


def sampler(args, positive, negative, latent, model):
    return {"class_type": "KSampler", "inputs": {"model": model, "seed": args.seed, "steps": args.steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": positive, "negative": negative, "latent_image": latent, "denoise": 1.0}}


def build_t2i(args):
    prompt = common_nodes(args)
    prompt["4"] = {"class_type": "FluxGuidance", "inputs": {"conditioning": ["2", 0], "guidance": 3.5}}
    prompt["7"] = sampler(args, ["4", 0], ["3", 0], ["6", 0], ["5", 0])
    return prompt


def build_redux(args):
    if not args.reference:
        raise ValueError("Redux requires --reference <image path>.")
    prompt = common_nodes(args)
    reference = stage_input(args.reference)
    prompt.update({
        "4": {"class_type": "LoadImage", "inputs": {"image": reference}},
        "10": {"class_type": "StyleModelLoader", "inputs": {"style_model_name": "flux1-redux-dev.safetensors"}},
        "11": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "sigclip_vision_patch14_384.safetensors"}},
        "12": {"class_type": "CLIPVisionEncode", "inputs": {"clip_vision": ["11", 0], "image": ["4", 0], "crop": "center"}},
        "13": {"class_type": "StyleModelApply", "inputs": {"conditioning": ["2", 0], "style_model": ["10", 0], "clip_vision_output": ["12", 0], "strength": 0.8, "strength_type": "attn_bias"}},
        "14": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["13", 0], "guidance": 3.5}},
    })
    prompt["7"] = sampler(args, ["14", 0], ["3", 0], ["6", 0], ["5", 0])
    return prompt


def build_fill(args):
    if not args.image or not args.mask:
        raise ValueError("Fill requires --image <image path> and --mask <mask path>.")
    image = stage_input(args.image)
    mask = stage_input(args.mask)
    prompt = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-fill-dev.safetensors", "weight_dtype": "default"}},
        "3": {"class_type": "LoadImage", "inputs": {"image": image}},
        "4": {"class_type": "LoadImageMask", "inputs": {"image": mask, "channel": "red"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": args.prompt, "clip": ["1", 1]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": args.negative, "clip": ["1", 1]}},
        "7": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["5", 0], "guidance": 3.5}},
        "8": {"class_type": "InpaintModelConditioning", "inputs": {"positive": ["7", 0], "negative": ["6", 0], "vae": ["1", 2], "pixels": ["3", 0], "mask": ["4", 0], "noise_mask": True}},
        "9": {"class_type": "ModelSamplingFlux", "inputs": {"model": ["2", 0], "max_shift": 1.15, "base_shift": 0.5, "width": args.width, "height": args.height}},
        "10": {"class_type": "KSampler", "inputs": {"model": ["9", 0], "seed": args.seed, "steps": args.steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": ["8", 0], "negative": ["8", 1], "latent_image": ["8", 2], "denoise": 1.0}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["1", 2]}},
        "12": {"class_type": "SaveImage", "inputs": {"images": ["11", 0], "filename_prefix": "codex_flux_fill"}},
    }
    return prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", choices=("t2i", "redux", "fill"), required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative", default="low quality, blurry, distorted anatomy, extra fingers, text, watermark")
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--reference")
    parser.add_argument("--image")
    parser.add_argument("--mask")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    prompt = {"t2i": build_t2i, "redux": build_redux, "fill": build_fill}[args.workflow](args)
    if args.dry_run:
        print(json.dumps(prompt, ensure_ascii=False))
        return
    api_json(f"{SERVER}/object_info")
    prompt_id = api_json(f"{SERVER}/prompt", {"prompt": prompt, "client_id": str(uuid.uuid4())})["prompt_id"]
    output_node = "12" if args.workflow == "fill" else "9"
    for _ in range(240):
        history = api_json(f"{SERVER}/history/{prompt_id}")
        result = history.get(prompt_id)
        if result:
            if result.get("status", {}).get("status_str") == "error":
                raise RuntimeError(json.dumps(result, ensure_ascii=False))
            images = result.get("outputs", {}).get(output_node, {}).get("images", [])
            if images:
                image = images[0]
                image["path"] = str(OUTPUT_DIR / image["subfolder"] / image["filename"])
                print(json.dumps({"prompt_id": prompt_id, "image": image}, ensure_ascii=False))
                return
        time.sleep(2)
    raise TimeoutError("ComfyUI did not finish within 8 minutes.")


if __name__ == "__main__":
    main()
