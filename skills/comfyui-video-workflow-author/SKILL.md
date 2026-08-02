---
name: comfyui-video-workflow-author
description: Use when creating, adapting, explaining, testing, or automating a ComfyUI video workflow, including Wan I2V, FLUX keyframes, ControlNet, PuLID, video API nodes, canvas workflow JSON, or ComfyUI `/prompt` API JSON. Generate matching importable canvas and API workflow artifacts, store reusable pairs, and explain nodes, generation principles, parameters, dependencies, and verification limits.
---

# ComfyUI 视频工作流编排

创建可编辑画布工作流与可执行 API 工作流的一对产物；说明清楚、可复用、可验证。不要把未验证的节点连线或平台能力说成可用。

## 固定位置与交付物

- 画布母版：`D:\Comfy-Desktop\ComfyUI-Shared\workflow-library\canvas\<slug>.json`
- API 执行副本：`D:\Comfy-Desktop\ComfyUI-Shared\workflow-library\api\<slug>.api.json`
- 随工作流交付的说明：与画布母版同目录的 `<slug>.说明.md`。从 `assets\workflow-说明-template.md` 复制并填满。
- 实际运行后才可增加 `<slug>.运行记录.md`，记录 seed、实际模型、输入资产、输出文件和验证范围。
- 本机 Desktop 可发现副本：`D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\user\default\workflows\<slug>.json`。它只用于侧边栏打开；母版仍以 Shared 的画布文件为准。

画布 JSON 是给用户在 ComfyUI 中查看、拖拽和继续编辑的母版。API JSON 是提交 `POST http://127.0.0.1:8188/prompt` 的节点输入图，不是同一种文件格式。

## 本机 API 自启

本机已配置名为 `ComfyUI Local API` 的当前用户登录任务。它运行 `D:\Comfy-Desktop\ComfyUI-Shared\scripts\Start-ComfyUI-Api.ps1`，使用 `ComfyUI\.venv\Scripts\python.exe` 启动后端，并且只监听 `127.0.0.1:8188`；不需要打开 Desktop 界面。

每次 API 工作前先请求 `/object_info`。若不可用，检查该任务状态并启动同名任务；不要改写任务、启动脚本、端口或监听地址，除非用户明确要求。登录后冷启动约需半分钟；API 返回 200 才能提交工作流。

## 工作流前置检查

1. 阅读当前项目的 `AGENTS.md`、README、分镜/计划和资产状态；遵守其中优先级与提交规则。
2. 明确镜头目标、输入资产顺序、模型、时长/帧数、分辨率、连续性要求和验收标准。需要同机位连续镜头时，先规划共享交界帧。
3. 查询本机 `http://127.0.0.1:8188/object_info`，据实际 `class_type`、输入字段和模型下拉值组织节点。API 不可用时，先报告“无法运行验证”，不要臆测安装状态。
4. 区分核心节点、已安装第三方节点与缺失节点。缺失节点或模型只报告 D 盘目标路径、容量和可信下载链接；未经用户授权不得安装或下载。
5. 外部视频 API 节点必须能显式传入模型 ID、关键参数与密钥的安全配置路径；不具备时说明能力缺口。不得把 API key 写入 JSON、说明或提示词。

## 结构引导素材补齐

当 PuLID + Union ControlNet 的镜头要求头盔、服装、道具、姿态或构图等可见结构，而当前 Canny/Depth/Pose 引导图没有该结构时，不要直接以提示词代替约束。按以下顺序主动补齐：

1. 搜索当前项目的授权角色卡、参考图、道具图和既有关键帧，优先选择同时匹配所需结构和镜头角度的素材；不得修改或覆盖原资产。
2. 从合适素材提取或生成对应的 Canny、Depth 或 Pose 引导；若结构与目标镜头不相符，使用确定性裁剪/合成仅制作新的引导副本，并保留来源记录。
3. 若项目资产没有足够的结构参考，使用内置 `image_gen` 生成仅用于 ControlNet 结构约束的参考图，再从该图生成引导。标记它为合成引导图，不得把它伪称为角色原始参考或最终交付图。
4. 每次尝试都把结构参考、最终引导图和输出并列展示，确认头盔/服装/道具轮廓实际进入引导图；最多完成两种合理引导方案。仍不能满足镜头要求时，再明确说明缺什么并请用户提供素材。

这条补齐流程不替代身份参考：PuLID 仍使用授权角色参考图，ControlNet 引导只承担姿态、构图和可见结构约束。

## 节点方案与成对生成

先给用户一个简短节点方案和验收标准，再写入文件；用户确认后才搭建新复杂工作流。按任务选择最少必要节点：

| 需求 | 优先结构 |
| --- | --- |
| 角色一致关键帧 + 姿态/构图 | 参考图 → PuLID-Flux → FLUX Union ControlNet → 图像输出 |
| 本地 Wan 图生视频 | 首帧 → Wan I2V 高/低噪声阶段 → 采样 → VAE 解码 → 视频合成 |
| 相邻镜头无切换 | 前镜尾帧 = 后镜首帧；入口不支持尾帧时明确标注 |
| 精确文字、价格、余额、商品 UI | 使用确定性后期合成；不要让生成模型重画 |
| 第三方视频服务 | 素材 → 显式 model/duration/resolution/audio → API 节点 → 输出 |

画布文件和 API 文件必须表达同一逻辑。优先由已验证的画布母版导出 API 格式；无法导出时，依据本机 `object_info` 生成 API 图，并把“由节点签名生成、尚未在画布反向验证”写进说明。

画布母版变更后，由 Codex 重新生成或重新导出同名 API 副本并更新说明。用户不维护两份文件；用户手动改画布后，只需提出“同步 <slug> 工作流”。不要分别手改两份而造成漂移。

## 参数说明要求

在每份说明中按实际节点解释这些项；未使用的项不要伪造：

- **模型与 LoRA**：决定能力与视觉先验；LoRA 权重越高，风格/动作约束越强，也越可能压制原始构图或产生过拟合。
- **提示词、负面提示词、参考图**：提示词定义意图，参考图定义可见锚点；精确 UI 文本不属于可靠生成目标。
- **采样器、步数、CFG**：步数增加通常更慢且存在收益递减；CFG 过高容易生硬、过低容易偏题。只给所用模型的实测或文档建议值。
- **seed**：固定 seed 只在模型、版本、节点、参数与硬件/随机实现相同的条件下有利于复现，不等于跨模型复现。
- **分辨率、帧数、fps**：分辨率主要影响细节与显存；帧数与 fps 决定时长；两者同时增大会显著提高耗时与显存。
- **首/尾帧、ControlNet、PuLID**：分别约束起止状态、姿态/构图、身份；强度过大可能抑制动作幅度或导致僵硬。

同时给出每项可安全调整的方向、对质量/速度/显存的影响及建议起点。不要以版本号大小替代能力判断。

## 验收与自动运行

1. 保存三件套后，先检查 JSON 可解析、节点 ID/输入连线有效、模型名与本机实际值匹配。
2. 仅在用户允许生成且 ComfyUI API 正常时，用 API JSON 做单镜 smoke test。允许替换的字段仅限说明中列出的首/尾帧、提示词、时长/分辨率、seed 等。
3. 记录实际输出、耗时、种子和错误。`任务接受`、`队列成功`、`节点不报错`只证明链路，不能证明画面质量、人物连续性或首尾帧合格。
4. 批量执行前，让用户确认单镜结果或明确授权；第三方服务提交仍须遵守项目的上下文提交包、模型选择和用户授权规则。
5. 需要声明 Desktop 画布通过时，将当前画布副本放入上述 Desktop 发现目录，在工作流侧边栏双击打开为独立标签，确认图形、连线可见且未出现缺失节点/模型提示。先新建空白标签，绝不覆盖用户已有未保存画布；这项验收仍不等于视觉质量通过。

Wan T2V 的原生入口没有参考图输入时，只能验收运行和基础语义，不能验收角色卡身份一致性。PuLID + Union 的 API 成功也只证明节点链路；必须把输出脸部与授权参考图并列人工检查，且 ControlNet 引导图必须实际包含要约束的服装/道具轮廓。Canvas/API 三件套和 API 输出不能替代在 Desktop 画布中打开、检查缺失节点/模型与连线的验收。

## 用户如何使用交付物

在说明中写出实际路径，并提供：

1. ComfyUI 画布：`Workflow → Open` 导入 `<slug>.json`，核对缺失节点/模型，替换已标注的输入后 Queue。
2. 自动执行：由 Codex 读取 `<slug>.api.json`，按说明替换允许字段，再提交本机 `/prompt`；不要把画布 JSON 直接当 API 请求体。
3. 自行修改画布后：保存画布母版并说“同步 <slug> 工作流”；由 Codex 生成匹配的 API 副本。

## 常见错误

- 不要为“看起来完整”而添加未安装的第三方节点。
- 不要将仅首帧约束的入口描述为首尾帧可控。
- 不要使用网络截图、旧工作流名或模型版本推断当前节点输入；以 `object_info` 和实际运行日志为准。
- 不要自动安装、下载或提交耗费算力/外部额度的任务；先取得授权。
