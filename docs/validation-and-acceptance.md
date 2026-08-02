# 验证与验收记录

本文件把已经完成的机器验收和必须等待用户素材的生产验收分开记录。没有实际素材、输出和人工复核时，不把链路检查表述为成片质量、身份稳定或语义正确。

## 已完成：运行环境

| 项目 | 证据 | 结论 |
| --- | --- | --- |
| ComfyUI 共享目录 | 后台启动参数显式使用 Shared 的 models、input、output；API 重启后模型下拉可见 | 已修复 |
| FLUX 文生图 | 固定 seed 424242，512x512，20 steps；两次输出为 codex_flux_t2i_00003_.png 和 codex_flux_t2i_00004_.png；ImageMagick AE 对比为 0 (0) | 已通过链路、基本画面与同环境可复现性验收 |
| PuLID / Union ControlNet | API 实际列出 pulid_flux_v0.9.0.safetensors 与 diffusion_pytorch_model.safetensors | 依赖已发现；未以人物素材验证身份/姿态效果 |
| Wan 2.1 T2V 1.3B | 官方 Comfy-Org 文件 2,838,303,560 字节；SHA-256 为 be531024cd9018cb5b48c40cfbb6a6191645b1c792eb8bf4f8c1c6e10f924dc5；API UNETLoader 可见 | 已安装和发现；未生成视频 |
| rembg 物体抠图 | isnet-general-use.onnx 为 178,648,008 字节；MD5 为 fc16ebd8b0c10d971d3513d564d01e29；Provider 首位为 CUDAExecutionProvider | 模型和 CUDA Session 已通过 |
| 视频学习根目录 | User 与当前 Process 的 VIDEO_LEARNING_ROOT 均为 D:\CodexVideoLearning；check_runtime.py 返回成功 | 已统一 |

说明：Wan 的旧 6 MiB 不完整文件保留为同目录明确的 .incomplete-20260802 备份，不是可扫描的 safetensors 模型；未删除用户数据。

## 待用户素材：生产验收

| 验收项 | 请提供 | 验收输出与通过标准 |
| --- | --- | --- |
| PuLID + Union ControlNet 关键帧 | 每角色 6–12 张授权参考图；目标姿态或构图参考；镜头规格 | 成对 Canvas/API 工作流、固定 seed 输出、人工复核表；身份不串人、姿态和构图达标 |
| Wan I2V | 已确认的首帧图；可选尾帧/前镜尾帧；时长、fps、分辨率、动作要求 | 单镜视频、运行记录、首尾帧对照；确认动作、连续性、闪烁和时长 |
| Wan T2V 1.3B | 一条可公开保存的测试提示词；时长、fps、分辨率目标 | 最小 T2V 工作流与单镜输出；仅验收可运行和基本语义，不代替成片质量 |
| 非人物 rembg | 1–3 张授权物体图，最好含复杂边缘 | RGBA PNG、原图/透明通道对照；主体完整、边缘无明显误切 |
| 视频理解、筛片、字幕翻译 | 一段可处理视频；若非中文，说明目标译文语言；若需下载，提供有权保存 URL | 原文 SRT/VTT、译文或双语 SRT、事件卡、关键帧、候选片段；时间码与原始音视频可回溯 |
| 已知人物识别 | Lightroom 目录或明确的人物参考图；独立人工标注测试视频 | 阈值校准记录、review candidate 表、Top-1/误认/漏检统计；不足阈值一律 unverified |
| GPT-SoVITS / RVC | 每角色 20–40 分钟单人、无音乐无混响、授权录音及逐字稿 | 训练权重、可选 index、保留内容换声样本；听感与授权双重复核 |
| MuseTalk | 授权人物视频或正脸图、授权驱动音频 | 成品视频与原音频；检查口型、身份、画面稳定性和不同步问题 |

## 交付规则

1. 新增 ComfyUI 复杂工作流必须保存 Canvas JSON、API JSON、说明 Markdown；首次执行后保存运行记录。
2. 每个生产验收记录输入资产顺序、模型与节点版本、提示词、seed、分辨率、帧数、fps、耗时、输出路径和人工结论。
3. 任何云端视频提交前先写或更新 视频生成任务上下文提交包.md；若不能显式选择用户指定模型，先说明缺口，不提交。
4. 原片、参考图、录音、模型、输出和密钥不进入本公开仓库。
