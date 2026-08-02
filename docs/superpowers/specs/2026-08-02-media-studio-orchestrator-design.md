# Media Studio Orchestrator 设计

## 目标

创建一个可自动发现的个人总控 Skill，安装位置为 C:\Users\J\.codex\skills\media-studio-orchestrator。它应在用户提出图片、视频、音频或视频理解任务时统一选择正确的本机或云端执行链路，并明确区分可运行、仅依赖存在、待素材验收和被权限阻塞的状态。

首版成功标准：

1. 用户不必记忆已有 9 个专用 Skill 的名字即可获得正确路由。
2. 每次任务先进行最小健康检查，再选择工具或服务，避免把模型文件存在误报为可调用。
3. 保留当前安全边界：凭据不输出、不入仓库；云端视频先写上下文提交包；需要用户素材、授权或模型选择时停在明确门槛。
4. 不复制模型、不创建新服务、不替换已验证的底层脚本或界面软件。
5. 当前 ComfyUI、rembg、视频学习和语音验证状态能以引用资料维护，而非散落在多个规则里。

## 非目标

- 首版不实现统一 Media MCP、任务队列、HTTP 服务或新的持久化数据库。
- 不删除或重写现有 ComfyUI、rembg、视频学习、语音等专用 Skill。
- 不自动下载模型、安装依赖、提交云端生成任务或消耗 GPU 批量算力。
- 不把用户素材、模型、输出、Cookie、Token 或 API Key 放入 Skill 或公开仓库。

## 方案选择

采用总控 Skill 包加底层执行器。

总控只处理任务分类、健康检查、路径和凭据边界、交付记录和验收；执行阶段调用现有专用 Skill、固定 CLI 或本地 HTTP API。这样保留专用 Skill 中已验证的节点、模型和工具细节，又为用户提供一个统一入口。

不采用单一超长 SKILL.md，因为路径、模型、服务状态和验收规则会使它难以维护。不在首版加入 Media MCP，因为应先取得实际 PuLID、Wan、字幕、声音等素材验收数据。

## Skill 包结构

    C:\Users\J\.codex\skills\media-studio-orchestrator\
    ├── SKILL.md
    ├── agents\openai.yaml
    └── references\
        ├── health-and-paths.md
        ├── image.md
        ├── video.md
        ├── audio.md
        └── acceptance.md

SKILL.md 保持在 350 行以内，只保留触发条件、路由表、强制门槛、统一交付状态和引用资料的读取条件。五份引用资料按任务类别按需读取，避免每次加载全部模型、命令和路径信息。首版不创建 scripts 目录：现有执行脚本已经由专用 Skill 维护，复制会造成两套实现漂移。

agents/openai.yaml 只提供显示名称、简短描述和默认提示语，不添加图标、品牌色或不必要字段。

## 触发与路由

Skill 描述必须覆盖：生图、改图、抠图、固定 seed、关键帧、生视频、图生视频、视频下载、视频学习/总结/识别/筛片、字幕/翻译、配音、克隆声音、换声、对口型、ComfyUI、FLUX、Wan、PuLID、ControlNet、RVC、GPT-SoVITS、MuseTalk、媒体工作流和统一媒体能力。

路由顺序：

1. 识别任务类型、输入资产、是否需要确定性结果、是否需要本地离线、是否有云端服务或模型要求。
2. 读取对应引用资料，执行只覆盖所需链路的健康检查。
3. 选择一个执行器；多个执行器可用时按下表优先级选择。
4. 检查授权、成本、模型选择、素材与验收门。
5. 执行或报告具体阻塞项；统一输出输入路径、执行器、模型/参数、输出、验证范围和后续素材要求。

| 需求 | 首选执行器 | 不适用时 |
| --- | --- | --- |
| 普通文生图、语义改图 | 内置 image_gen | 用户明确 CLI 时走 Kitool GPT Image |
| 确定性图像处理 | ImageMagick | Node 服务/Buffer/Stream 才用项目本地 Sharp |
| 人物/物体抠图 | CUDA rembg | 人物用 u2net_human_seg；物体用 isnet-general-use |
| 固定 seed、本地关键帧 | ComfyUI FLUX | 先核验 API、模型下拉与输出目录 |
| 身份 + 姿态/构图 | PuLID-Flux + FLUX Union ControlNet | 没有素材时建立验收项，不退化为单参考 Redux 承诺 |
| 本地 I2V/T2V | Wan 工作流 | 先核验模型、VAE、文本编码器、工作流与素材 |
| 视频下载/学习/粗剪 | download-videos → video-learning | 遵守平台授权、DRM 和 Cookie 边界 |
| 字幕与翻译 | ASR/OCR/视觉证据 → 原文字幕 → 翻译 → 双语字幕 | 翻译服务未验收时明确输出原文与缺口 |
| 文本配音/克隆 | VoxCPM2 或 GPT-SoVITS | 角色训练权重需要授权录音与逐字稿 |
| 已有录音换音色 | RVC | 缺少授权目标 .pth/.index 时阻塞 |
| 视频对口型 | MuseTalk | 需要授权肖像素材和驱动音频 |
| 云端图/视频/短剧 | Kitool、XYQ/Pippit、HeyGen | 先检查 Key、额度、显式模型选择和上下文提交包 |

## 健康与路径契约

health-and-paths.md 记录本机事实与检查方法：

- ComfyUI Local API 仅监听 127.0.0.1:8188；智能体未发现 API 时复用现有当前用户计划任务后台启动，Desktop 由用户手动可见启动。
- 共享 ComfyUI models、input、output 位于 D:\Comfy-Desktop\ComfyUI-Shared；API 必须实际列出所需模型。
- rembg 固定使用 D:\AI\rembg，拒绝 CPU fallback；物体模型已安装但图像质量仍须按素材验收。
- VIDEO_LEARNING_ROOT 固定为 D:\CodexVideoLearning；检查项目 venv、模型、OCR、视觉运行器和工具配置。
- 声音根目录为 D:\AI\Voice，MuseTalk 根目录为 D:\AI\Video\MuseTalk；不得混用引擎用途。
- 只记录凭据是否存在和安全载体，绝不读取或展示值。

健康检查返回四级状态：ready、partial、missing、blocked。只有 ready 才可提交对应本地工作流；partial 必须说明缺项；missing 只报告下载链接、目标 D 盘路径和预计容量；blocked 指向授权、素材、模型选择或外部可访问性。

## 安全与授权门

1. 图片生成默认内置 image_gen；用户明确要求 CLI 才使用 Kitool。
2. 任何 Node 项目需要 Sharp 时，先征得项目本地依赖安装同意。
3. 云端视频、即梦、Seedance、小云雀提交前，先创建或更新项目内的视频生成任务上下文提交包.md。用户指定模型而入口不能显式选择时，不提交。
4. Hugging Face 受限模型仅通过 Windows 凭据帮助脚本注入当前进程 Token；不输出、不保存、不改写 Token。
5. 下载只处理用户有权保存的媒体；不绕过 DRM、付费、登录、地区或访问控制；不导出 Cookie。
6. 人脸、声音、肖像、驱动音频均需用户本人或明确授权。没有授权或输入素材时，记录验收需要，不生成。

## 验收与记录

acceptance.md 提供统一记录字段：任务 ID、输入资产顺序、执行器、模型/节点版本、提示词、seed、分辨率、帧数、fps、耗时、输出路径、证据、人工结论、状态和未解决风险。

验收严格分层：

- API/模型下拉可见：仅证明发现。
- 任务接受、队列成功、节点无报错：仅证明链路。
- 输出文件存在、元数据正确、像素比较通过：证明技术输出。
- 人工画面/音频复核与独立测试集：才证明身份、姿态、运动、字幕、翻译或声音质量。

首版引用仓库 docs/validation-and-acceptance.md 的素材清单，并要求在未来真实任务完成后更新本机运行记录，不将验收模板当作结果。

## 实现与验证

实现顺序：

1. 使用 skill-creator 的初始化脚本创建 Skill 包、references 与 agents 元数据。
2. 编写 SKILL.md 和五份引用资料；从当前已验证配置和全局规则提炼，避免复制无关历史。
3. 用 quick_validate.py 校验前言、命名、目录和 UI 元数据。
4. 以四个只读压力场景检查路由：普通生成式改图、物体抠图、带非中文字幕的视频学习、带身份和姿态要求的 Wan 关键帧。
5. 不执行生成、下载、云端提交或用户素材处理；压力场景只验证决策是否选择正确执行器和门槛。

复杂 Skill 的独立 forward-test 可能触及本机服务或生成任务。首版不自动启动子代理测试；待本 Skill 完成且用户批准后，再以不执行实际生成的只读任务进行验证。
