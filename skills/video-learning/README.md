# 视频理解、筛片、粗剪与信息提取 Skill

让 Codex 处理本地视频、文件夹、可授权保存的公开视频、授权网页播放与 Insta360 素材，交付可复核的学习笔记、事件卡、精彩/互动/对话候选和派生候选片段。所有结论必须带时间码和证据边界；学习笔记只是交付形式之一。

## 能力与边界

| 能力 | 当前状态 | 说明 |
|---|---|---|
| 本地视频/文件夹、可访问 URL | 可用 | 可处理多个输入；可授权保存时优先保存完整本地视频。 |
| 字幕、音频转写、OCR、关键帧 | 可用 | 并行取证，不能只靠任一来源下结论；分析/粗剪会生成外挂 SRT。 |
| 已拼接 360 MP4 | 已验证 | 可全片四视角人脸复核、活动/人脸候选排序、证据帧、360 master 与 1080p 平滑观看版导出。 |
| Lightroom 人物参考库、姓名候选 | 已验证（复核级） | 可建立同模型 embedding、校准 review threshold，并在平面视频中给出连续出镜候选；不会自动确认姓名。 |
| 批量筛片与粗剪 | 已验证 | 普通或已拼接 360 本地视频可按批次连续处理；每源独立输出候选、报告、派生母版和适用的观看版。姓名仅复核级；说话人仍需独立证据。 |
| 原始 `.insv` 指定帧/完整拼接 | 已验证 | 官方 Desktop Media SDK 已验证指定帧和完整 2:1 H.265/AAC MP4；SDK 原生指定起止时间 MP4 仍未提供。 |
| 原始 `.insv` 文件夹自动筛片 | 已实现 | 递归枚举、每个原片独立 SDK 拼接、接入批量筛片，并写源文件—母版—下游状态清单；不合并录像。 |

不绕过 DRM、付费、验证码、登录、地区或反自动化限制；不自动导出浏览器 Cookie、令牌或密码。原始视频、`.insv`、Lightroom Catalog 和源照片不被修改或覆盖。

## 原理

```text
视频/授权网页
  -> 完整本地副本，或已验证的播放采集
  -> 字幕 + 完整时间码音频 + 原始高分辨率关键帧 + OCR
  -> 场景/运动事件与自适应覆盖
  -> 本地视觉模型、GPU 人脸候选、交叉验证
  -> 事件卡 / 学习笔记 / 筛片清单 / 派生候选片段
```

- 音频、OCR、画面和视觉模型是并行证据，不是互相替代的后备方案。
- 粗扫可用低分辨率和 GPU 加速；最终提帧、OCR、视觉复核仍使用原始高分辨率素材。
- 连续骑行等没有硬切换的画面，使用时长和运动自适应覆盖锚点；不使用固定 15 秒作为主策略。
- 原始转写永远保留。ASR 不通顺、重复或与画面矛盾时，拒绝把它写成事实。
- 人脸同框不等于人物身份；人物同框不等于说话人归属。后两者必须有独立参考证据。

## 资源、成本与硬件

基础工具均免费、开源或免费可下载；本地路线不产生云端 API 按量费。Codex 阅读转写、分析关键帧、排序和写报告仍会消耗当前 Codex 对话的 token；FFmpeg、Whisper、OCR 和人脸检测主要消耗本机算力、磁盘和时间。

| 类别 | 资源 | 建议 |
|---|---|---|
| 必需 | [FFmpeg](https://ffmpeg.org/download.html)（含 FFprobe） | 检查媒体、抽音频、关键帧、导出。确保 `ffmpeg` 与 `ffprobe` 在 `PATH`。 |
| 必需 | Python 3.10–3.13 | 建议专用虚拟环境。当前 Python 3.13 已验证标准检测、关键点和 512 维识别 embedding；可不安装其可选 3D mask-rendering 扩展。 |
| 转写 | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | `large-v3-turbo` 适合作为中文最终识别起点；CPU 可用，NVIDIA GPU 更快。 |
| OCR | [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) + `chi_sim` | 同时安装 OCR 引擎、语言数据和 Python `pytesseract`。 |
| URL | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 只用于有权访问且可保存的媒体。 |
| 网页播放采集 | [VB-CABLE](https://vb-audio.com/Cable/) | 仅当完整文件与可访问音频流不可得时需要。 |
| 人脸候选（可选） | [InsightFace](https://github.com/deepinsight/insightface)、OpenCV、`antelopev2` | GPU 路线还需要与显卡驱动兼容的 ONNX Runtime CUDA 包和 CUDA wheel DLL；只加入当前 Python 进程，不改系统 `PATH`。 |
| 本地视觉理解（可选） | [llama.cpp](https://github.com/ggml-org/llama.cpp) 多模态 CUDA 构建 + [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) | 需要与运行器兼容的 GGUF 模型和 projector；不属于本仓库的一键安装。 |
| 非中文外挂字幕翻译（可选） | `llama-cli` + Qwen2.5 文本 GGUF | 批量翻成简体中文，不调用收费 API；若运行器或模型不可用，仍输出原文 SRT 并标明状态。 |
| 原始 `.insv`（可选） | [Insta360 Desktop Media SDK 申请](https://www.insta360.com/cn/sdk/apply) + [官方 C++ 示例](https://github.com/Insta360Develop/Desktop-MediaSDK-Cpp) | 需要 SDK、Visual Studio Build Tools 2022（MSVC v143 + Windows SDK）和受控的子进程 DLL 路径。 |

建议为模型、原片和派生产物预留至少 30 GB；5.7K 360 原片与中间帧会明显增加磁盘占用。4090 等 24 GB 显存显卡适合同时处理转写、视觉模型和 GPU 人脸候选，但不改变证据边界。

## 安装与目录配置（Windows）

安装 Skill：

```powershell
git clone https://github.com/swedenjiang-Gh/video-learning-skill.git "$env:USERPROFILE\.codex\skills\video-learning"
```

选择非系统盘工作目录。下例使用 `D:\VideoLearning`，可改为任何本地路径：

```powershell
$env:VIDEO_LEARNING_ROOT = 'D:\VideoLearning'
New-Item -ItemType Directory -Force "$env:VIDEO_LEARNING_ROOT\venv", "$env:VIDEO_LEARNING_ROOT\models", "$env:VIDEO_LEARNING_ROOT\work", "$env:VIDEO_LEARNING_ROOT\downloads", "$env:VIDEO_LEARNING_ROOT\reference-data" | Out-Null
python -m venv "$env:VIDEO_LEARNING_ROOT\venv"
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" -m pip install faster-whisper pytesseract numpy
```

若希望每次新终端自动使用同一目录，在 PowerShell 中执行一次：

```powershell
setx VIDEO_LEARNING_ROOT "D:\VideoLearning"
```

重新打开终端后生效。`scripts/check_runtime.py` 会读取该变量；未设置时兼容旧默认值 `D:\CodexVideoLearning`。不要把模型、视频、转写、Cookie 或令牌提交到 Git。

### 可选 GPU 转写

安装与 NVIDIA 驱动、CUDA 版本匹配的 `ctranslate2`/CUDA 运行时后，使用：

```python
WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
```

模型首次运行会下载。离线或受限网络环境可从对应 Hugging Face 模型页预先下载到模型缓存目录；受限模型的 token 必须放在凭据/环境变量中，不能写进仓库。

### 可选 GPU 人脸候选

需要 OpenCV、InsightFace、GPU ONNX Runtime 与 `antelopev2` 模型。先在小批量画面确认每个 ONNX 模型实际使用 `CUDAExecutionProvider`；若回退到 CPU，不得把它当作 GPU 结果。Lightroom 人物标注不能直接作为视频模型 embedding，必须从可访问的已标注照片建立同模型参考库。

### 可选官方 Insta360 Desktop Media SDK

只用于原始 `.insv` 的官方拼接，不提交 SDK 的 DLL、模型、压缩包或编译产物。将 SDK 解压到非系统盘，例如 `D:\VideoLearning\tools\insta360-media-sdk\MediaSDK`；安装 Visual Studio Build Tools 2022，并选择 MSVC v143、Windows SDK 和 CMake 工具。

SDK 自带 C++ 示例 `example\main.cc`，需要链接 `lib\MediaSDK.lib` 并在运行时将 `bin` 仅加入该子进程 `PATH`。建议把编译出的官方 Demo 放入工作目录，并设置：

```powershell
$env:INSTA360_MEDIA_SDK_ROOT = 'D:\VideoLearning\tools\insta360-media-sdk\MediaSDK'
$env:INSTA360_MEDIA_SDK_DEMO = 'D:\VideoLearning\work\insta360-sdk\MediaSDKDemo.exe'
```

Windows 官方 Demo 已验证可将原片的指定帧拼接为 2:1 JPEG，也已验证完整 2:1 H.265/AAC 导出。公开的 3.1.3 头文件和 Demo 未提供指定起止时间直接导出 MP4 的接口；不能将帧导出误作原生区间粗剪。不同机型、保护镜和 AI 拼接设置仍须以实际输出复核。

完整的 Windows、Tesseract、VB-CABLE、CUDA DLL 与本地视觉模型配置见 [references/runtime-setup.md](references/runtime-setup.md)。

## 验证环境

```powershell
$env:VIDEO_LEARNING_ROOT = 'D:\VideoLearning'
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" scripts\check_runtime.py
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" -m unittest discover -s tests -p "test_*.py"
```

`check_runtime.py` 只报告工具、包和配置路径，不会安装或修改系统。运行结果中的 `configured_runtime` 为 `false` 时，先检查 `VIDEO_LEARNING_ROOT`、文件位置与可执行文件 `PATH`。

## 使用方式

### 在 Codex 中

直接提供一个或多个本地文件、文件夹或 URL，并说出目标。例如：

```text
筛选 D:\Footage 中的 MP4：找出脸完整清晰、两人同框和有对话的候选，保留原片，输出候选片段和 Markdown 报告。
```

```text
学习这个授权视频链接：优先下载完整本地副本，提取字幕、转写、OCR、关键帧和视觉证据，给我可复核的中文笔记。
```

### 直接运行脚本

```powershell
# 展开本地文件/文件夹，不修改来源
python scripts\list_media.py D:\Footage D:\Downloads\lesson.mp4

# 查看流信息并区分普通媒体、已拼接 360、原始/未知 .insv
python scripts\inspect_media.py D:\Footage\VID_001.insv

# 全时轴变化粗扫；CUDA 仅用于粗扫，最终证据仍取原始分辨率
python scripts\scan_events.py D:\Footage\stitched-360.mp4 --scan-width 160 --scan-fps 2 --hwaccel cuda --output D:\VideoLearning\work\events.json

# 从 360 事件区间投影出前/右/后/左视角
python scripts\extract_360_views.py D:\Footage\stitched-360.mp4 D:\VideoLearning\work\events.json D:\VideoLearning\work\views --width 1920 --height 1080

# 已验证的官方 SDK 原片 selected-frame export；输出目录必须是新目录
python scripts\insta360_sdk_frames.py --inputs F:\Insta360\VID_001.insv --output-dir D:\VideoLearning\work\sdk-frames --frames 0 900 1800 --output-size 3840x1920

# `work` 可清理：长期复用的 Lightroom 索引与人脸 embedding 必须放入 reference-data。
$referenceRoot = 'D:\VideoLearning\reference-data\lightroom\current-catalog'

# 只读导出 Lightroom 的全部人物、照片和人脸框；catalog 只从指定工作目录中选择
python scripts\export_lightroom_people_index.py --catalog D:\Lightroom\Current\Current.lrcat --output "$referenceRoot\people-index"

# 建立同一 InsightFace 模型的参考库、校准复核阈值
python scripts\build_face_reference.py --faces-csv "$referenceRoot\people-index\people-faces.csv" --output-dir "$referenceRoot\face-reference" --model-root D:\VideoLearning\models\face-recognition
python scripts\calibrate_face_threshold.py --reference-dir "$referenceRoot\face-reference" --output "$referenceRoot\face-reference\threshold-calibration.json"

# 扫描普通视频或已重构的平面视角；姓名结果只用于复核候选
python scripts\scan_known_faces.py D:\Footage\flat-view.mp4 --reference-dir "$referenceRoot\face-reference" --model-root D:\VideoLearning\models\face-recognition --output D:\VideoLearning\work\known-faces.json --threshold 0.60

# 本地 VAD + large-v3-turbo 时间码原始转写；须通过质量门后才可写入结论
python scripts\dialogue_candidates.py D:\Footage\clip.mp4 --model-path D:\VideoLearning\models\faster-whisper-large-v3-turbo --output D:\VideoLearning\work\dialogue.json

# 根据候选清单导出精确 H.265/AAC 派生片段；原片不修改
python scripts\export_candidate_clips.py D:\Footage\stitched-360.mp4 D:\VideoLearning\work\known-faces.json D:\VideoLearning\work\candidate-clips --padding 1

# 批量完成已拼接 360/普通视频的筛片、候选导出、报告与 360 观看版；每次使用新的 output-root
python scripts\screen_video_batch.py D:\Footage\a.mp4 D:\Footage\stitched-360.mp4 --output-root D:\VideoLearning\work\screening-batch --reference-dir D:\VideoLearning\work\face-reference --model-root D:\VideoLearning\models\face-recognition --threshold 0.60 --dialogue-model D:\VideoLearning\models\faster-whisper-large-v3-turbo

# 原始 Insta360 文件夹：逐个官方 SDK 拼接，再连续筛片；输出根目录必须是新目录
python scripts\screen_insta360_folder.py F:\Insta360\to-screen --output-root D:\VideoLearning\work\insta360-folder-screening --sdk-root D:\VideoLearning\tools\insta360-media-sdk\MediaSDK --demo-exe D:\VideoLearning\work\insta360-sdk\MediaSDKDemo.exe --reference-dir D:\VideoLearning\reference-data\lightroom\current\face-reference --model-root D:\VideoLearning\models\face-recognition --threshold 0.60

# 已完成拼接但下游筛片中断时：复用已有 stitched 母版并新建 screening-resume-###，不会覆盖旧产物
python scripts\screen_insta360_folder.py F:\Insta360\to-screen --output-root D:\VideoLearning\work\insta360-folder-screening --sdk-root D:\VideoLearning\tools\insta360-media-sdk\MediaSDK --demo-exe D:\VideoLearning\work\insta360-sdk\MediaSDKDemo.exe --reference-dir D:\VideoLearning\reference-data\lightroom\current\face-reference --model-root D:\VideoLearning\models\face-recognition --threshold 0.60 --resume
```

对授权网页：先尝试平台字幕或完整本地副本；仅在两者不可得时，把**播放应用本身**路由到 VB-CABLE，运行 `python scripts\check_capture.py --verify` 确认 `CABLE Output` 有真实信号，再开始播放采集。不要改变系统默认扬声器，也不要同时混入其他应用音频。

### 外挂字幕与自动翻译

指定 `--dialogue-model` 后，每个源输出目录都会生成 `source.srt`；每个 `360 master candidate` 和 `reframed candidate` MP4 旁都会生成同名 `.srt`。候选字幕从完整原始时间轴裁切并归零，不会重新转写。

- 检测语言为中文：SRT 保留原始 ASR 文本。
- 其他语言：每条 SRT 显示“原文 + 简体中文译文”两行。默认读取 `$env:VIDEO_LEARNING_ROOT\vision\runtime\llama-cli.exe` 与 `translation\models\qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf`；也可用 `--translation-runner` 和 `--translation-model` 覆盖运行器与模型路径。
- `delivery.json` 的 `subtitles.translation` 记录源语言、目标语言、翻译条数和 `complete` / `partial` / `blocked_missing_local_translator`。原始 `dialogue.json` 不改写；翻译不能纠正听写错误，也不能单独确认术语、命令或事实。

默认的高质量本地翻译模型为 Qwen2.5-7B-Instruct Q8_0，约 7.75 GB，拆成 3 个文件。放到 `D:\CodexVideoLearning\translation\models\`（目录已创建），保持文件名不变；只需要下载一次：

- [00001（3.98 GB）](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf?download=true)
- [00002（3.94 GB）](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q8_0-00002-of-00003.gguf?download=true)
- [00003（176 MB）](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q8_0-00003-of-00003.gguf?download=true)

原始发布页：[Qwen/Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)。下载齐 3 个分片后仅把第一个分片路径传给 `llama-cli`；运行器会自动读取后续分片。该模型只承担翻译，现有 Qwen2.5-VL 和 projector 继续专用于画面理解。

### Insta360 工作流

1. 保留原始 `.insv`。
2. 用 `inspect_media.py` 判断：已拼接 2:1 全景可直接处理；一个或多个双鱼眼/未知 `.insv` 位于文件夹内时，在 SDK 根目录、官方 Demo 和真实机型路由均已验证后，优先用 `screen_insta360_folder.py` 逐个导出完整高质量 2:1 母版并直接筛片；否则用 Studio 导出高质量、非重构 2:1 全景副本。原始文件之间不拼接。
3. 360 事件必须检查重叠的前、右、后、左投影视图，必要时再检查上、下方向。
4. 候选导出先保留 `360 master candidate`；`reframed candidate` 仅在人物/事件跟随与平滑取景已验证后交付，绝不能替代完整全景母版。

## 交付与证据等级

每批次输出 `complete`、`partial` 或 `blocked` 状态，并按请求提供学习笔记、事件卡、精彩候选、互动/对话候选、候选片段或全景粗剪。

- `confirmed`：直接由可见画面、清晰 OCR 或经验证音频确认。
- `partial`：证据存在但覆盖/质量不完整。
- `likely`：多个线索支持但仍需复核。
- `unverified`：不得写成结论。

对话候选需要时间码语音与画面交叉支持。说话人归属需要声纹参考或嘴形/发声时间同步等独立证据；仅凭同框人脸不能归属句子。

## V2 讨论与路线图

独立人物命名验收、质量门通过的对话事实、可靠说话人归属、SDK 与 Studio 画质对比和网页中断恢复的详细前置与验收标准见 [references/v2-pending-design.md](references/v2-pending-design.md)。该文档记录设计和待办，不代表现有能力。

## 开发与发布检查

```powershell
python -m unittest discover -s tests -p "test_*.py"
python C:\Users\<you>\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```

提交前确认不包含视频、模型、转写、工作目录、凭据或安装包；只提交 skill、脚本、测试与文档。
