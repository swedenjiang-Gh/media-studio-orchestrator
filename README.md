# Codex Local Media Studio

本仓库记录这台 Windows 工作站截至 **2026-08-02** 的图片、视频、音频、视频理解能力，以及它们的调用边界、实际路径、容量和待修复项。它是未来“媒体总控 Skill / Media MCP”的事实基线；不包含模型、用户素材、Cookie、Token 或 API Key。

## 先看结论

| 领域 | 可直接使用 | 当前限制 |
| --- | --- | --- |
| 常规生图/生成式改图 | Codex `image_gen`；用户明确要求 CLI 时可走 Kitool GPT-Image-2 | Kitool 属云 API，需已配置的 Key 和额度 |
| 本地可复现生图 | FLUX.1-dev、Redux、Fill 文件齐全 | 8188 API 当前只识别到部分 UNET/CLIP；Checkpoint、ControlNet、PuLID 下拉为空 |
| 确定性修图 | ImageMagick；Node 项目内用 Sharp | 生成式修改不应走这两者 |
| 本地抠图 | CUDA rembg + `u2net_human_seg`（人物） | `isnet-general-use.onnx` 缺失，非人物物体抠图未补齐 |
| 本地图生视频 | Wan 2.2 I2V 模型文件在盘 | 需要修通 ComfyUI 模型路径、保存 Canvas/API 工作流并 smoke test |
| 视频下载/理解/筛片 | 受授权下载、FFmpeg、Whisper、OCR、Qwen-VL、InsightFace、Insta360 SDK 工作流 | 翻译与双语字幕尚未形成验收过的自动化链路 |
| 本地配音/换声/对口型 | VoxCPM2、GPT-SoVITS、RVC、MuseTalk 环境均在 | RVC/GPT-SoVITS 没有已训练的角色专属权重 |
| 云端图/视频/短剧 | Kitool、XYQ/Pippit、小云雀、HeyGen 连接器 | Key、额度、模型选择与云端结果均需每次按入口核验 |

详细能力与调用方式见 [docs/local-media-inventory.md](docs/local-media-inventory.md)，容量和凭据状态见 [docs/storage-and-credentials.md](docs/storage-and-credentials.md)。

## 调用总线

```mermaid
flowchart TD
  A["用户媒体任务"] --> B{"总控 Skill 路由"}
  B --> C["image_gen / Kitool"]
  B --> D["ImageMagick / Sharp / rembg"]
  B --> E["ComfyUI API: FLUX / PuLID / Wan"]
  B --> F["download-videos → video-learning"]
  B --> G["VoxCPM2 / GPT-SoVITS / RVC / MuseTalk"]
  B --> H["XYQ / Pippit / HeyGen"]
  E --> I["统一工作流库、输入输出目录、任务日志"]
  F --> J["字幕、OCR、视觉理解、候选片段"]
```

未来应建设一个“总控大 Skill”，只负责任务分类、健康检查、统一路径、任务记录和验收；保留现有专用 Skill/CLI/API 作为执行器。把所有实现细节硬塞进一个超长 `SKILL.md` 会造成重复规则和难以维护的分支。

## 当前最高优先级

1. 修复 ComfyUI API 对 `D:\Comfy-Desktop\ComfyUI-Shared\models` 的加载，并统一输入/输出路径；通过 FLUX、PuLID + Union ControlNet、Wan I2V 三个单镜 smoke test。
2. 将 `VIDEO_LEARNING_ROOT` 统一设置为 `D:\CodexVideoLearning`，淘汰文档中的旧示例 `D:\VideoLearning`。
3. 补齐约 176 MiB 的 `isnet-general-use.onnx` 到 `D:\AI\rembg\models`，并验证一个非人物物体抠图。
4. 先建立 Canvas/API 成对工作流和运行记录，再考虑统一 Media MCP。

这些动作会改变本机配置、下载模型或消耗 GPU，因此不随本次盘点自动执行。

## 安全与仓库边界

- 本仓库公开，但只存文档、工作流模板和无敏感测试样例。
- API Key、Token、Cookie、`.env`、用户素材、模型、缓存、输出和训练权重均不得提交。
- 云端视频提交前必须先编写或更新项目内《视频生成任务上下文提交包.md》；只有入口能显式选择或可靠约束用户指定模型时才提交。
- 人脸、声音、视频和下载内容必须具有用户本人或明确授权；不绕过 DRM、付费、登录、地区或反自动化限制。

## 文档目录

- [本机媒体能力清单](docs/local-media-inventory.md)：Skill、软件、模型、节点、服务、SDK、调用链路与验收状态。
- [存储与凭据状态](docs/storage-and-credentials.md)：实测容量、模型尺寸、程序路径、环境变量与安全配置位置。
