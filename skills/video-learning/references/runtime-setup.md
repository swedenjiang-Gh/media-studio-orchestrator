# Windows 运行环境配置参考

本文件描述可复现的本地配置，不安装任何软件。示例根目录使用 `D:\VideoLearning`；可用任意非系统盘路径，并通过 `VIDEO_LEARNING_ROOT` 指定。不要把该目录中的原片、模型、转写、工作产物或凭据提交到 Git。

## 目录布局

```text
D:\VideoLearning
├── venv\          Python 虚拟环境
├── models\        Whisper、人脸和视觉模型
├── bin\           可选的 yt-dlp 等便携工具
├── work\          音频、帧、OCR、转写和报告等派生产物
└── downloads\     授权下载的视频
```

```powershell
$env:VIDEO_LEARNING_ROOT = 'D:\VideoLearning'
```

`scripts/check_runtime.py` 使用该变量检查 `venv`、`bin`、`Tesseract-OCR` 与可选视觉模型路径。未设置时，它仅为兼容旧部署而回退至 `D:\CodexVideoLearning`。

## FFmpeg 与 URL 工具

安装 FFmpeg 后确认：

```powershell
ffmpeg -version
ffprobe -version
```

可将 `yt-dlp.exe` 放入 `$env:VIDEO_LEARNING_ROOT\bin`，或放入 `PATH`。它只用于有权访问且可保存的媒体；不传递 Cookie、不绕过限制。

## Python、Whisper 与 OCR

建议使用 Python 3.10–3.12：

```powershell
python -m venv "$env:VIDEO_LEARNING_ROOT\venv"
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" -m pip install faster-whisper pytesseract numpy
```

安装 Tesseract 引擎和所需语言数据（中文通常为 `chi_sim`）。如果 `tesseract.exe` 不在 `PATH`，在调用前显式设置 Python bridge：

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"D:\VideoLearning\Tesseract-OCR\tesseract.exe"
```

OCR 只确认可读文字；命令、数字或产品名不清晰时保留 `[OCR uncertain]`，不要猜测修正。

## NVIDIA GPU 与 Faster-Whisper

GPU 不是必需条件，但能显著缩短长视频转写。先确认驱动与显卡：

```powershell
nvidia-smi
```

安装与本机驱动/CUDA 兼容的 CTranslate2、CUDA runtime wheel 或其他官方支持的运行时。CUDA DLL 应只加入**当前 Python 进程**，不写系统 `PATH`。若 wheel 将 DLL 放在 `site-packages\nvidia\*\bin`，可在启动 Python 前动态加入：

```powershell
$sitePackages = "$env:VIDEO_LEARNING_ROOT\venv\Lib\site-packages\nvidia"
$cudaBins = Get-ChildItem -LiteralPath $sitePackages -Directory | ForEach-Object {
  Join-Path $_.FullName 'bin'
} | Where-Object { Test-Path -LiteralPath $_ }
$env:PATH = ($cudaBins + $env:PATH) -join ';'
```

然后用小样本验证：

```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
segments, info = model.transcribe("sample.mp4", language="zh")
for segment in segments:
    print(segment.start, segment.end, segment.text)
```

模型首次下载或离线缓存可放在 `$env:VIDEO_LEARNING_ROOT\models`。受限 Hugging Face 模型使用用户的安全凭据/进程环境变量；不要把 token 输出到终端、日志、源码或配置。

## GPU 人脸候选

这是可选能力，适合“脸完整清晰”“同框”“已建立参考库的人物出现”等候选筛选。

```powershell
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" -m pip install opencv-python-headless insightface onnxruntime-gpu
```

还需下载 `antelopev2` 模型到本地模型根。先在少量帧上确认模型实际 provider 为 `CUDAExecutionProvider`，并拒绝静默 CPU 回退。Python 3.13 的 InsightFace 兼容性可能需要本地补丁；新部署优先 Python 3.11/3.12。

Lightroom Catalog 只能以只读方式导出人物和照片索引。其内部人脸特征不能直接和 InsightFace 比较：需要从可访问的已标注原始照片提取相同模型的 embedding，并在保留视频上校准阈值后才可输出姓名。

## 本地视觉模型

视觉模型用于补足画面中的场景、动作、人物、物体和屏幕上下文，必须与字幕、音频和 OCR 同时间轴交叉核验。可选择 llama.cpp 的 CUDA 多模态运行器配合 Qwen2.5-VL 兼容 GGUF 模型和 projector。

- 启动前先用单张图确认运行器可加载模型和 GPU。
- 每次输入同一短时间段内按顺序排列的关键帧，并在外部保留真实时间码。
- 提示模型只描述可见内容与不确定性；不要求它猜身份、意图、未出现的事件或对话。
- 模型文件通常较大，应置于 `models`；不同 GGUF 量化、projector 与运行器版本必须匹配。

本仓库不提供视觉运行器/模型的一键安装脚本，避免把特定显卡、量化和模型许可误当作通用配置。

## VB-CABLE 网页播放采集

仅在完整视频、平台字幕和可访问音频流不可得时使用：

1. 安装 VB-CABLE，确认输出设备为 `CABLE Input`，录音设备为 `CABLE Output`。
2. 在 Windows 应用音量/设备首选项中，仅将 Codex/Chrome 的**目标播放应用**输出改为 `CABLE Input`；系统默认扬声器和其他应用保持原样。
3. 视频正在播放时运行：

   ```powershell
   python scripts\check_capture.py --verify
   ```

4. 只有输出同时显示设备可用且 `has_signal: true` 时才录制。录音在播放/跳转前开始，在第一遍播放结束时停止，避免循环尾音。
5. 每段记录播放器 `currentTime`、录音起点和检查点。用户跳转进度条或播放中断时创建新段，不把前后音频伪装为连续时间轴。

该路线只记录用户有权播放的正常音频，不绕过 DRM、付费、登录或地区限制。

## Insta360

- 原始 `.insv` 始终保留。
- 用 `scripts/inspect_media.py` 检查是否已经是带 equirectangular 标记的 2:1 全景；是则可直接分析。
- 原始双鱼眼或未知 `.insv`，先经 Insta360 Studio 导出高质量、非重构 2:1 全景副本；不要把 16:9 重构视图当作 360 母版。
- 官方 Desktop Media SDK 只有在获批、安装、并用真实文件验证后才能用于批量拼接、selected-frame 或区间导出。社区 CLI 不能替代该验证。

## 运行前检查

```powershell
& "$env:VIDEO_LEARNING_ROOT\venv\Scripts\python.exe" scripts\check_runtime.py
python scripts\check_capture.py --verify   # 仅网页播放采集时
```

任何组件缺失时先报告缺口、下载来源、目标目录和容量，再安装；安装包完成后应删除，保留模型与配置。
