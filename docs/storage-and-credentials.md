# 存储、软件路径与凭据状态

快照日期：2026-08-02。容量以递归文件总和统计，单位 GiB；不包含显存占用，不代表目录内所有文件都是不可替代依赖。模型、用户媒体和输出均不应提交到本仓库。

本次变更后，Comfy 共享模型目录为 84.864 GiB，rembg 目录为 3.910 GiB，列出目录的合计为 193.563 GiB。Wan 1.3B 与 isnet-general-use 的校验记录见 validation-and-acceptance.md。

## 目录容量

| 路径 | 容量 | 内容/用途 |
| --- | ---: | --- |
| D:\Comfy-Desktop\ComfyUI-Shared\models | 84.864 | ComfyUI 模型共享库；包含 Wan 换新后的 2.643 GiB 正式文件与 6 MiB 不完整备份 |
| D:\Comfy-Desktop\ComfyUI-Installs | 6.861 | ComfyUI 后端、节点、运行环境 |
| D:\Program Files\Comfy Desktop | 0.472 | Comfy Desktop GUI |
| D:\AI\rembg | 3.910 | CUDA rembg、Python venv、人物与非人物抠图模型 |
| D:\CodexVideoLearning | 53.867 | 视频学习环境、模型、参考库与工作产物；工作产物可增长 |
| D:\AI\Voice\VoxCPM2 | 8.113 | VoxCPM2、CUDA 环境与模型 |
| D:\AI\Voice\GPT-SoVITS | 11.756 | GPT-SoVITS 基础权重、运行环境 |
| D:\AI\Voice\RVC | 11.074 | RVC 基础资产、CUDA 环境 |
| D:\AI\Video\MuseTalk | 12.569 | MuseTalk 权重、运行环境 |
| D:\Tools\CodexVideoDownloader | 0.017 | 下载工具包装目录 |
| C:\Program Files\ImageMagick-7.1.2-Q16-HDRI | 0.060 | ImageMagick 程序 |
| **上述目录合计** | **193.563** | 仅列出的运行目录，未计用户下载、素材、缓存和输出 |

## 关键模型文件

| 模型 | 路径 | 容量 | 作用 / 状态 |
| --- | --- | ---: | --- |
| FLUX.1-dev FP8 | models\checkpoints\flux1-dev-fp8.safetensors | 16.062 GiB | 本地非商用文生图；文件有效，当前 API 下拉已识别；固定 seed 文生图链路已冒烟验证 |
| FLUX Fill | models\diffusion_models\flux1-fill-dev.safetensors | 22.170 GiB | 蒙版定稿精修；慢，当前 API 链路未验收 |
| FLUX Redux | models\style_models\flux1-redux-dev.safetensors | 0.120 GiB | 参考图构图/色调辅助，不保证身份 |
| SigCLIP vision | models\clip_vision\sigclip_vision_patch14_384.safetensors | 0.798 GiB | Redux 视觉编码器 |
| PuLID-Flux | models\pulid\pulid_flux_v0.9.0.safetensors | 1.064 GiB | 身份保持；当前 API 下拉已识别；尚未以人物素材验收身份效果 |
| FLUX Union ControlNet | models\controlnet | 约 6.150 GiB | 姿态/构图控制；当前 API 下拉已识别；尚未以姿态/构图素材验收效果 |
| Wan 2.2 I2V high / low | models\diffusion_models\wan2.2_i2v_*_14B_fp8_scaled.safetensors | 各 13.313 GiB | 本地图生视频两阶段模型 |
| Wan LightX2V LoRA high / low | models\loras\wan2.2_i2v_lightx2v_4steps_lora_v1_*.safetensors | 各 1.143 GiB | Wan 加速 LoRA |
| UMT5 XXL FP8 | models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors | 6.273 GiB | Wan 文本编码器 |
| Wan VAE | models\vae\wan_2.1_vae.safetensors | 0.236 GiB | Wan 解码 |
| Wan 2.1 T2V 1.3B | models\diffusion_models\wan2.1_t2v_1.3B_fp16.safetensors | 2.643 GiB | 正式文件已校验，API 可发现；尚未完成 T2V 生成验收 |
| rembg 人像 | D:\AI\rembg\models\u2net_human_seg.onnx | 167.8 MiB | 已存在，人物抠图 CUDA 路线 |
| rembg 物体 | D:\AI\rembg\models\isnet-general-use.onnx | 170.4 MiB | 已安装、MD5 校验，并以 CUDA Provider 验证 |
| Whisper large-v3-turbo | D:\CodexVideoLearning 下的模型目录 | 1.507 GiB | CUDA 转写 |
| Qwen2.5-VL-7B Q8 + projector | D:\CodexVideoLearning 下的模型目录 | 7.542 + 1.261 GiB | 本地视觉理解 |
| VoxCPM2 主模型 + AudioVAE | D:\AI\Voice\VoxCPM2 | 4.266 + 0.351 GiB | 本地语音生成/参考音色 |
| MuseTalk UNet / SyncNet / Whisper / VAE / DWPose | D:\AI\Video\MuseTalk | 3.167 / 1.386 / 0.141 / 0.312 / 0.379 GiB | 口型同步基础模型 |

## API Key、Token、Cookie 与连接器

只记录存在性、用途和安全位置；**不读取、不输出、不写入任何值**。

| 服务 | 当前状态 | 配置位置 / 方式 | 使用边界 |
| --- | --- | --- | --- |
| Kitool GPT-Image-2 | 已配置 | C:\Users\J\.kitool\config.json 的私有 api_key 字段 | 仅 CLI GPT Image；不得提交该文件 |
| XYQ / 小云雀 | 已配置 | XYQ_ACCESS_KEY：当前 Process 与 User 环境变量均存在 | 用于云端图/视频/短剧；不可写入脚本、工作流 JSON 或仓库 |
| OpenAI API | 未配置 | OPENAI_API_KEY 在 Process/User/Machine 均未设置 | 若未来选用 OpenAI API，需要由用户安全配置，不影响 Codex 内置能力 |
| Hugging Face | 当前进程 Token 存在 | 优先 Windows 通用凭据 Codex.HuggingFace.ReadToken，经 C:\Users\J\.codex\scripts\Get-HuggingFaceReadToken.ps1 注入进程 | 仅受限模型下载；不打印、不持久化、不改写 |
| HeyGen | 连接器已可用 | 由 MCP/连接器安全管理 | 不记录本地明文密钥路径 |
| yt-dlp / BBDown 登录态 | 可能按网站需要 | 仅复用用户已登录浏览器会话，不读取、导出、保存或打印 Cookie | 不绕过 DRM、付费或访问控制 |
| ComfyUI 远程视频节点 | 节点可能存在，密钥/额度未核验 | 每家服务独立安全配置 | 必须能显式传模型 ID/参数才可承诺指定模型 |

## 路径统一与下一步修改建议

1. 用户环境变量 VIDEO_LEARNING_ROOT 已设置为 D:\CodexVideoLearning；后续脚本统一从变量取根目录，不再使用旧例 D:\VideoLearning。
2. ComfyUI 使用一个共享模型目录 D:\Comfy-Desktop\ComfyUI-Shared\models，通过后端额外模型路径配置加载，避免复制 82.221 GiB。
3. ComfyUI 的 API 输入、输出与 submit_comfy_workflow.py 必须统一；输出、缓存和用户素材默认不进入 Git。
4. 如下载 isnet-general-use.onnx 或重下 Wan 1.3B，事前记录来源、目标 D 盘目录、预计容量和校验方式；下载完成后删除安装包，不删除用户现有资产。
