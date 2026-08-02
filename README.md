# Codex Local Media Studio

本仓库版本化这台 Windows 工作站的媒体 Skill：总控、图像、ComfyUI、视频学习/字幕、音频与小云雀执行器。它不包含模型、用户素材、Cookie、Token 或 API Key。

当前可安装的本地 Skill 快照见 [skills/README.md](skills/README.md)。`docs/` 中带日期的早期盘点保留为历史证据；当前行为、路径门禁和验收边界以同步后的 `skills/` 内容为准。

## 先看结论

| 领域 | 可直接使用 | 当前限制 |
| --- | --- | --- |
| 常规生图/生成式改图 | Codex `image_gen`；用户明确要求 CLI 时可走 Kitool GPT-Image-2 | Kitool 属云 API，需已配置的 Key 和额度 |
| 本地可复现生图 | FLUX.1-dev、Redux、Fill；ComfyUI API 和 Desktop 画布均已验证 | FLUX.1-dev 仅限非商用；Redux 不承诺人物身份一致性 |
| 确定性修图 | ImageMagick；Node 项目内用 Sharp | 生成式修改不应走这两者 |
| 本地抠图 | CUDA rembg：`u2net_human_seg`（人物）、`isnet-general-use`（物体） | alpha matting 仍须逐图目检光晕/雾影 |
| 本地图生视频 | Wan 2.2 I2V 与 Wan 2.1 T2V 1.3B 已有 Canvas/API 对、实际运行与 Desktop 导入验收 | 仅低分辨率 smoke；生产分辨率、长镜和角色一致性仍需镜头验收 |
| 视频下载/理解/筛片 | 受授权下载、FFmpeg、Whisper、OCR、Qwen-VL、InsightFace、Insta360 SDK；英语→简中双语外置 SRT 已实测 | 无平台字幕的翻译仍需逐源质量复核；内封/烧录字幕尚未验收 |
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

总控 Skill 已实现为 [`skills/media-studio-orchestrator`](skills/media-studio-orchestrator)。它只负责任务分类、健康检查、统一路径、任务记录和验收；专用 Skill/CLI/API 仍是执行器。不要把所有实现细节复制进总控文件。

## 本次完成与后续

1. 已完成：ComfyUI API 共享模型、输入与输出路径修复；FLUX 固定 seed 冒烟图通过。
2. 已完成：VIDEO_LEARNING_ROOT 已统一为 D:\CodexVideoLearning，并已通过运行时自检。
3. 已完成：isnet-general-use.onnx 已下载、校验并用 CUDA Provider 验证。
4. 已完成：Wan 1.3B 已从官方 ComfyUI 仓库重新下载、SHA-256 校验并被 API 发现。
5. 已完成：PuLID + Union、Wan I2V、Wan T2V 工作流三件套已保存、API 实跑并在 Desktop 画布导入；PuLID 人脸视觉质量仍未通过。
6. 后续：收到用户授权的人物图、关键帧、视频或录音后，按验收记录完成生产质量验证。

需要素材的验收项目及交付标准见 docs/validation-and-acceptance.md。

## 安全与仓库边界

- 本仓库公开，只存可审阅的 Skill、文档、工作流模板和无敏感测试样例。
- API Key、Token、Cookie、`.env`、用户素材、模型、缓存、输出和训练权重均不得提交。
- 云端视频提交前必须先编写或更新项目内《视频生成任务上下文提交包.md》；只有入口能显式选择或可靠约束用户指定模型时才提交。
- 人脸、声音、视频和下载内容必须具有用户本人或明确授权；不绕过 DRM、付费、登录、地区或反自动化限制。

## 文档目录

- [本机媒体能力清单](docs/local-media-inventory.md)：Skill、软件、模型、节点、服务、SDK、调用链路与验收状态。
- [存储与凭据状态](docs/storage-and-credentials.md)：实测容量、模型尺寸、程序路径、环境变量与安全配置位置。
- [验证与验收记录](docs/validation-and-acceptance.md)：已完成的机器验证，以及等待用户素材的生产验收清单。
- [Skill 安装与清单](skills/README.md)：已同步的 Skill、来源目录、安装位置与未纳入的插件缓存。
- [媒体入口规则](docs/media-entrypoint.md)：需要加入全局 `AGENTS.md` 的最小总控入口规则。
