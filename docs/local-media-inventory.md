# 本机媒体能力清单

快照日期：2026-08-02。状态定义：**可运行**表示本轮有直接运行证据；**部分可运行**表示服务或依赖只完成一部分；**文件存在**不等于已接通调用链路。

## 图片

| 能力 / Skill | 适用场景 | 调用与依赖 | 当前状态 |
| --- | --- | --- | --- |
| imagegen（内置） | 默认文生图、生成式编辑、补全/换物/改风格 | Codex 内置 image_gen；不依赖本地模型 | 路由默认值；本轮工具上下文未暴露调用器，未实测 |
| gpt-image | 用户明确要求 CLI 生图或图生图 | Node.js → C:\Users\J\.codex\skills\gpt-image\scripts\generate.js → Kitool GPT-Image-2；默认 2K | 私有 API Key 已配置；云端付费/额度链路，未提交生成任务 |
| imagemagick-image-editing | 裁剪、缩放、拼接、蒙版、透明度、文字、格式、像素比对 | magick.exe；绝对路径；修改后 identify + 视觉检查 | 可运行，ImageMagick 7.1.2-27 |
| sharp-node-image-processing | Node 服务、Buffer/Stream、高吞吐缩略图/格式转换 | 交付代码应依赖项目本地 sharp；全局 Sharp 仅临时命令 | 全局 sharp@0.35.3 已安装；修改项目依赖前须征得同意 |
| rembg-background-removal | 语义抠图、透明 PNG、视频前景素材 | D:\AI\rembg\venv\Scripts\python.exe + D:\AI\rembg\remove-background.py | 人物 u2net_human_seg CUDA 模型可用；物体模型缺失 |
| comfyui-local-image-workflows | 离线、固定 seed、参考图构图/色调、批量统一关键帧 | ComfyUI 127.0.0.1:8188、FLUX/Redux/Fill、submit_comfy_workflow.py | API 在线但模型加载不完整；不能误报为可自动出图 |

### 图片路由规则

1. 普通生图/生成式编辑优先内置 image_gen。
2. 用户明确“用 CLI 生图”时走 Kitool GPT Image，默认 2K。
3. 像素结果可明确描述时用 ImageMagick；不要为一次性任务编写 Pillow、System.Drawing、Python 或 Node 脚本。
4. 只有交付 Node 项目、需要 Buffer/Stream/服务端吞吐时才用 Sharp；先询问是否给项目安装本地依赖。
5. 人像/角色抠图用 u2net_human_seg；非人物主体用 isnet-general-use；仅发丝、毛发、半透明边缘才启用 alpha matting。
6. 仅在固定 seed、离线、可复现或 AI 视频关键帧批量一致时走 ComfyUI。FLUX.1-dev 非商用；Fill 慢，仅小范围定稿精修。

### FLUX / 角色一致性关键帧

身份一致与姿态/构图同时要求时，目标结构为：参考图 → PuLID-Flux → FLUX Union ControlNet → FLUX 输出。Redux 只能辅助参考，不能承诺身份保持；Fill 不是身份控制替代品。

FLUX 已验证的节点逻辑是：CheckpointLoaderSimple → CLIP 正/负提示词 → FluxGuidance → KSampler → VAEDecode → SaveImage，且 ModelSamplingFlux 与 EmptyLatentImage 尺寸一致、为 8 的倍数。当前 API 未列出 Checkpoint/PuLID/ControlNet 模型，因此先修配置再使用此图。

## 本地视频生成与云端视频

| 能力 / Skill | 功能 | 调用链路 | 状态 |
| --- | --- | --- | --- |
| comfyui-video-workflow-author | Wan I2V、FLUX 关键帧、PuLID、Union ControlNet、Canvas/API JSON | Canvas/API 应成对存于 D:\Comfy-Desktop\ComfyUI-Shared\workflow-library\canvas 和 api | 目录目前没有可复用工作流；未 smoke test |
| Wan 2.2 I2V | 首帧/关键帧驱动本地视频 | 高噪 + 低噪 14B → VAE → 视频合成 | 模型在盘，API 路径未验通 |
| Wan 2.1 T2V 1.3B | 轻量纯文本视频预演 | T2V 工作流 | 当前文件仅 0.006 GiB 且校验失败；不可用。只有需要纯 T2V 才建议重下 |
| xyq-skill | 小云雀云端图、文生视频、图生视频、视频编辑/续写/MV | 上传图片/视频/mp3/wav → asset_id → submit_run.py → 轮询 → 下载 | XYQ_ACCESS_KEY 已在 Process/User 层；提交前先写上下文包 |
| xyq-short-drama-skill | 短剧：剧本、场景、角色、分镜、成片 | pippit-tool-cli short-drama 提交、轮询、列文件、下载资产 | CLI 已装；Access Key 可用；模型/额度逐任务核验 |
| HeyGen 插件 | 云端数字人、口播视频 | 已连接的 HeyGen MCP/连接器管理身份与请求 | 连接器凭据不落本地文档；本次未提交任务 |

### ComfyUI API 与 Desktop 模式

已有计划任务 ComfyUI Local API，通过隐藏脚本 D:\Comfy-Desktop\ComfyUI-Shared\scripts\Start-ComfyUI-Api-hidden.vbs 启动；后端目录为 D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI，仅监听 127.0.0.1:8188。这符合“智能体 API 后台运行”；用户手动打开 Comfy Desktop 时保持可见。两种模式必须复用已有服务，不能抢同一端口。

本轮 API 在线；UNETLoader 识别 4 项、CLIPLoader 识别 25 项，但 CheckpointLoaderSimple、ControlNetLoader、PulidFluxModelLoader 模型下拉为 0。共享模型目录未被完整加载，或模型类别映射不匹配。修复应通过后端的 --extra-model-paths-config 指向共享 models，并统一提交脚本、API 输入输出目录；不要复制 82 GiB 模型。

### 工作流交付与验收

新增复杂工作流应有：Canvas JSON、API JSON、说明 Markdown；实际运行后再附运行记录。最低顺序为：JSON/模型名与 /object_info 匹配 → 固定 seed FLUX smoke test → PuLID + Union ControlNet 单图 smoke test → Wan I2V 单镜 smoke test。记录输入、seed、时长、显存/耗时、输出；队列成功不代表画质、身份连续性或首尾帧已验收。

## 视频下载、理解、识别、筛片、字幕

| 部件 | 能力 | 本机调用链路 |
| --- | --- | --- |
| download-videos | Bilibili、YouTube、抖音、X 等授权下载 | download-video.ps1：Bilibili/b23 用 BBDown，其余走 D 盘 yt-dlp 环境；默认 D:\VideoDownloads |
| video-learning | 本地/URL/360 视频学习、时间轴摘要、候选片段、粗剪、OCR、人物/对话候选 | check_runtime.py → list_media.py → ffprobe/字幕/音频/帧 → Whisper/OCR/Qwen-VL/InsightFace → 事件卡/报告 |
| Faster-Whisper | 时间码 ASR、VAD、对话候选 | large-v3-turbo + CUDA fp16；原始转写保留，开头/中间/结尾做质量门 |
| Qwen2.5-VL | 关键帧视觉理解 | 按时间排列关键帧；只描述可见人/物/动作/屏幕与不确定性 |
| Tesseract | 画面 OCR | 已有 161 语言数据；模糊文字标 [OCR uncertain]，不猜命令/数字 |
| InsightFace + Lightroom 参考库 | 已知人物复核候选 | 只读索引 → 同模型重建 512 维 embedding → 校准阈值 → review_candidate，不直接断言姓名 |
| FFmpeg / ffprobe | 探测、抽音频、抽帧、字幕封装、候选片段导出 | 所有派生产物保留真实时间码与源文件路径 |
| jianying-last-frame | 剪映草稿或视频最后一帧 | extract_last_frame.py 优先源视频抽帧；复杂叠层草稿须经 UI/导出验证 |
| Insta360 Desktop Media SDK | 原始 .insv selected-frame、整段拼接 | 官方 C++ Demo / insta360_sdk_frames.py；原片不改，保持 2:1 equirectangular 母版 |

字幕完整链路应为：授权下载/本地视频 → stream 探测与嵌入字幕保留 → ASR 时间轴 SRT/VTT → OCR/视觉交叉核验 → 原文字幕 → 本地或云端翻译 → 中文/双语 SRT → FFmpeg 软字幕或烧录。当前下载、ASR、OCR、视觉理解具备基础；自动翻译提供方及字幕工作流尚未验收。

网页播放采集仅在完整视频与平台字幕不可得时启用：目标应用单独输出到 VB-CABLE，确认 has_signal: true 后再由 FFmpeg 录制；不改系统默认扬声器、不读取或导出 Cookie、不绕过 DRM。

## 音频、配音、换声、对口型

| 引擎 | 用途 | 本机入口 | 当前边界 |
| --- | --- | --- | --- |
| VoxCPM2 | 从文本生成多语音色；可用授权参考音频克隆音色 | D:\AI\Voice\VoxCPM2\generate.py + 专用 CUDA venv | 现有模型可用；有参考音频和准确文本时相似度更高 |
| GPT-SoVITS | 角色声音数据集训练/GUI 推理 | D:\AI\Voice\GPT-SoVITS\GPT-SoVITS-v3lora-20250228\go-webui.bat；可选 API 9880 | 基础权重在；9880 未监听；没有角色训练权重 |
| RVC | 保留原录音内容与节奏，换授权目标音色 | D:\AI\Voice\RVC\.venv\Scripts\python.exe webui.py --noautoopen --port 7865 | 基础资产在；7865 未监听；需目标 .pth，可选 .index |
| MuseTalk v1.5 | 已有视频/人物图 + 驱动音频的口型同步 | D:\AI\Video\MuseTalk\run-lipsync.py | 127.0.0.1:7860 在线；正常任务走 CLI，不覆盖目标文件 |

人物录音可以作为起点，但不是无条件的一键生产资产：VoxCPM2 可用短参考音频；GPT-SoVITS/RVC 要长期稳定角色，建议每人准备 20–40 分钟干净、单人、无音乐/混响的授权录音及逐字稿。RVC 训练后生成 .pth，可选检索 .index。对口型不训练声音模型，而是需要已授权的肖像素材与驱动音频。

## 软件、运行环境、SDK 与 IDE 边界

| 类别 | 已验证组件 | 用途 |
| --- | --- | --- |
| GPU | NVIDIA GeForce RTX 4090 24 GiB，驱动 610.62 | Comfy、Whisper、InsightFace、语音/口型 GPU 推理 |
| Python | 3.13.14：C:\Users\J\AppData\Local\Programs\Python\Python313\python.exe | 各项目各自 venv；不混用全局包 |
| Node | 24.16.0：C:\Program Files\nodejs\node.exe | Kitool、Pippit、Sharp |
| FFmpeg | 8.1.1：C:\Users\J\AppData\Local\Programs\ffmpeg\ffmpeg-8.1.1-full_build\bin | 视频/音频编码、探测、字幕、抽帧 |
| ImageMagick | 7.1.2-27：C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe | 确定性图像处理 |
| Comfy Desktop | GUI：D:\Program Files\Comfy Desktop；后端：D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI | 画布编辑与本地 API |
| Pippit CLI | 1.0.10：C:\Users\J\AppData\Roaming\npm\pippit-tool-cli.ps1 | XYQ/小云雀任务；提示可升级到 1.0.17，本次未升级 |
| Insta360 SDK | Desktop MediaSDK 3.1.3.1 + 官方 Demo | 编译需 VS Build Tools 2022 MSVC v143 与 Windows SDK |

不要求特定 IDE 才能运行这些能力；IDE 仅用于维护工作流、Python/Node 或未来 MCP 代码。运行时依赖必须以项目 venv/项目 node_modules 为准，不能依赖 IDE 或机器全局包。

## 统一 Media MCP 的边界

MCP 应做受控编排层，不取代引擎：提供 health、submit、status、fetch_result、list_capabilities，内部再调用本地 HTTP API 或固定 CLI wrapper。它需要统一任务 ID、输出目录、模型/Key 可用状态、日志、队列和权限边界。前置条件是先修通 ComfyUI 并完成三条最小工作流；否则 MCP 只会把路径问题包装起来。
