# V2 讨论、待办与外部前置

本文件保存已经讨论、但尚未完整实现或尚未验证的设计。它不是能力清单：只有 `SKILL.md` 中已验证的流程才可直接承诺。每次实现后，将简洁的可执行规则迁入 `SKILL.md`，将验收结果留在对应工作目录。

## 已验证的基础

- 已拼接的 2:1 equirectangular 360 MP4 可直接分析；无需再经 Insta360 Studio。
- 4090 可完成 CUDA 全时轴粗扫、全景多视角投影、InsightFace GPU 人脸检测与无重编码 `360 master candidate` 导出。
- Lightroom 人物索引可只读导出，并可构建同模型人脸参考 embedding；阈值校准和视频结果均只产生复核候选，不能直接确认姓名。
- 完整音频可用本地 `large-v3-turbo` + VAD 转写为时间码候选，但结果必须通过语义质量门禁；风噪或环境声导致的重复/失真文本不能写成对话结论。
- 已拼接 360 的本地批处理已端到端验证：全片四视角人脸复核、活动/人脸候选合并排序、代表帧、360 master、1920x1080 H.265 观看版和 Markdown 报告均输出到隔离目录。

## 已验证基础：人物参考库

目标：把 Lightroom Classic 的人物标注转为本地视频人脸识别的参考库。

- 先以 SQLite 只读方式导出 Lightroom 的人物、照片和脸框索引；不写入 `.lrcat`，不改原始照片。
- Lightroom 的内部人脸特征不可与 InsightFace embedding 混用。必须从可访问的原始照片或导出的人脸裁剪建立同一模型的 512 维参考 embedding。
- `scripts/build_face_reference.py` 通过模型检测框与 Lightroom 标注框匹配，建立同一模型的 512 维 embedding；缺失照片、过小脸和未匹配脸保留计数但不进入库。
- `scripts/calibrate_face_threshold.py` 以留出的人物库样本估计保守的 review threshold；`scripts/scan_known_faces.py` 只输出 `review_candidate` 或 `unverified`。已在一个短的 360 重构平面视角上端到端验证。
- 用独立人工复核过的视频帧继续校准阈值；低于阈值或互相接近的结果一律标为 `unverified`。

未完成验收：可在独立、人工复核的视频上稳定把“已知人物”与“未知/不确定人物”区分；未达标时只交付人脸清晰度和同框候选，不输出姓名。

## 已验证基础：普通与已拼接 360 视频粗剪

目标：批量找出清晰完整人脸、用户指定人物、互动、动作/场景变化和对话候选，并导出派生片段，不覆盖原片。

1. 先以全时轴低分辨率变化信号和时长/运动自适应覆盖锚点建立候选；连续骑行等画面没有硬切换时不得判定“无内容”，也不得退化为固定 15 秒抽帧。
2. 对候选时间段提取原始分辨率画面；360 素材必须检查重叠的前/右/后/左视角，必要时加上/下视角。
3. 在候选段内做持续人脸检测、跟踪与质量评分，结合人脸面积、完整度、清晰度、持续时间、同框关系、动作/场景变化和已校准的人物匹配排序。
4. 输出事件卡：实际开始/峰值/结束、代表帧、直接可见事实、转写/OCR 证据、置信边界与复核优先级。
5. 对每个保留区间导出 `360 master candidate`：2:1 equirectangular、保留音频、记录源时间码和实际切点。关键帧 copy 切点不精确时记录实际范围；帧精确边界需重编码或经验证的 SDK 路线。
6. `reframed candidate` 是单独的观看版 MP4，需要人物/事件跟随、平滑 yaw/pitch/FOV 和可复核的时间轴；不能拿它替代 360 master。

已确认的交付约定：每个保留区间同时交付 `360 master candidate` 与 `reframed candidate`。前者保持原始 `3840x1920` H.265/AAC 全景内容；后者默认编码为 `1920x1080` H.265、20 Mbps、保留原音频。观看版只服务浏览和复核，绝不替换母版或删除原片。

已验证：`screen_video_batch.py` 已在真实已拼接 360 片段上产出独立批次清单、候选 JSON、Markdown 报告、四方向代表帧、H.265/AAC `360 master candidate` 和 1920x1080/20 Mbps H.265/AAC `reframed candidate`。观看版由连续复核人脸框推导 yaw/pitch，旋转命令按 0.1 秒插值；它是复核辅助，不确认身份、关系或说话人。

仍待验收：长时素材的人脸跨视角关联/遮挡恢复、不同机位下排序稳定性，以及更复杂运动中的观看版主观稳定性。

## 可直接推进：对话候选与说话人边界

目标：找出有对话的片段，避免把环境声、风噪或 ASR 幻觉写成内容。

- `scripts/dialogue_candidates.py` 已验证使用 CUDA `large-v3-turbo` + VAD 生成整段时间码原始转写和复核候选；明显重复会标为 `rejected`，其他输出为 `needs_manual_or_cross_modal_review`，不会自动通过事实质量门。
- 可选增加降噪，但降噪输出只是辅助转写输入；原始音轨必须保留。
- 只在时间码、转写和可见互动相互支持时标为 `对话候选`；音频可确认“有人说话”，画面可确认“谁在同框”，两者都不能单独证明是谁说的。
- 说话人归属需要独立证据：用户提供的干净声纹参考，或可复核的嘴形/发声时间同步。多人同框、人脸相似或用户关系描述都不足以归属句子。

未完成验收：输出经质量门通过的可复核对话候选时间段、原始转写与画面证据；没有独立说话人证据时，批处理明确写 `blocked_missing_independent_voice_or_mouth_evidence`。可靠归属仍需用户提供干净声纹参考或另行验证口型同步。

## 已验证：原始 Insta360 `.insv` 的官方 selected-frame export

官方 [Desktop-MediaSDK-Cpp](https://github.com/Insta360Develop/Desktop-MediaSDK-Cpp) 已安装并验证；不是社区 CLI，也没有使用 Studio 的内部服务。

- 本机版本：MediaSDK 3.1.3.1；GPU 版，Windows x64。编译官方 `example/main.cc` 需要 Visual Studio Build Tools 2022 的 MSVC v143 和 Windows SDK；运行时 DLL 只加入子进程 `PATH`，不写入系统 PATH。
- 真实验证源：用户提供的本地 `327_001.insv`，约 30 分钟，两个 HEVC `2880x2880` 视频流、AAC 音频和数据流。
- 官方 Demo 以 `optflow` 成功从该原片导出帧号 `0`、`26970`、`53900` 的 `3840x1920` JPEG；三帧均为不同时间位置且已正确拼接。可复用入口是 `scripts/insta360_sdk_frames.py`，实际导出必须写入新的工作目录，原 `.insv` 不改动。
- 同一真实源已完成 AI Stitch + FlowState 请求的整段导出：`3840x1920` equirectangular、H.265、约 60 Mbps、AAC 音频、29:59.8 时长，首/中/末画面均正常。当前公开头文件与 Windows Demo 仍没有 `start/end` 时间范围的 MP4 导出接口；不能把它说成已具备的 SDK 原生区间粗剪。

仍待验证：

1. 完整 SDK 输出与 Insta360 Studio 对应输出的投影、音频、时间码和画面质量对比。
2. 指定时间段候选片段：当前路线是先用 selected-frame export 筛选，再在完整、已验证的 360 母版上以 FFmpeg 导出；若厂商后续提供区间 MP4 API，再单独验证接入。
3. 对一个或两个输入 `.insv` 的机型规则、保护镜/潜水壳设置和 AI 拼接的质量/速度取舍。

Studio 仍是未验证源或完整母版导出的备用路线；`studio-exporter-service.exe` 和社区工具不作为已验证 CLI。保留版仍必须是 `2:1 equirectangular`、保留音频，并记录源时间码、实际切点、编码和码率。

## 网页视频可靠性增强

- 播放前验证目标应用已独立路由到 VB-CABLE，且 `CABLE Output` 有真实信号；不得只因设备存在就开始录音。
- 每段采集记录录音起点与播放器 `currentTime`；用户拖动进度条或播放中断时，停止当前段并建立独立段，禁止把两段音频硬拼成连续时间轴。
- 持久队列记录 `queued`、`running`、`complete`、`partial`、`blocked`；中断从最后确认检查点恢复，达到重试上限后明确标记 `blocked`。
- 音画对齐按每个采集段用多个 `currentTime` 观测拟合偏移与速率；不足两个观测的对齐必须标记为 provisional。
