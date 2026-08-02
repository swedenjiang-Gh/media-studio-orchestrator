# <工作流名称> 使用说明

## 用途与验收

- 目标镜头：
- 输入资产与顺序：
- 输出：
- 验收标准：
- 已知能力缺口：

## 文件

- 画布母版：`D:\Comfy-Desktop\ComfyUI-Shared\workflow-library\canvas\<slug>.json`
- API 副本：`D:\Comfy-Desktop\ComfyUI-Shared\workflow-library\api\<slug>.api.json`

## 节点与原理

| 节点 | 作用 | 关键输入 | 输出/影响 |
| --- | --- | --- | --- |
|  |  |  |  |

按实际数据流解释：输入素材如何被编码、约束、采样、解码并合成为视频。不得把未验证能力写成已支持。

## 参数

| 参数 | 当前值 | 调高/调低的影响 | 建议调整方式 |
| --- | --- | --- | --- |
| 模型 / LoRA |  |  |  |
| prompt / negative prompt |  |  |  |
| seed |  |  |  |
| steps / CFG / sampler |  |  |  |
| 分辨率 / 帧数 / fps |  |  |  |
| 首尾帧 / ControlNet / PuLID |  |  |  |

## 模型与节点依赖

- 已验证存在：
- 需要安装或下载：
- 模型路径：

## 导入与运行

1. 在 ComfyUI 选择 `Workflow → Open`，导入画布母版。
2. 核对模型和节点没有缺失；仅替换标注为可替换的输入。
3. Queue 单镜测试，检查输出是否满足验收标准。
4. 自动运行时，使用 API 副本提交 `/prompt`；不可直接提交画布 JSON。

## 验证记录

- 验证状态：未运行 / 链路已验证 / 画面已验收
- 实际模型与版本：
- seed：
- 输出路径：
- 证据与限制：
