# 本地媒体 Skill 快照

本目录是 `C:\Users\J\.codex\skills` 中媒体相关 Skill 的可版本化副本。将每个子目录复制到目标机器的 `%USERPROFILE%\.codex\skills\`，并将 `agents-skills/` 下的 Skill 复制到 `%USERPROFILE%\.agents\skills\`。

## 已同步

- 总控：`media-studio-orchestrator`
- 图像：`gpt-image`、`imagemagick-image-editing`、`sharp-node-image-processing`、`rembg-background-removal`、`comfyui-local-image-workflows`
- ComfyUI 视频/关键帧：`comfyui-video-workflow-author`
- 视频：`download-videos`、`video-learning`、`insta360-rename`、`jianying-last-frame`
- 音频：`local-voice-studio`
- 小云雀：`../agents-skills/xyq-skill`、`../agents-skills/xyq-short-drama-skill`

`imagegen`、HeyGen 等由 Codex 系统或插件提供，不在此复制；安装相应运行时/插件后，由总控 Skill 路由调用。

## 同步原则

`media-studio-orchestrator` 是入口和验收索引；各子 Skill 是命令、参数、模型路径和执行细节的单一事实来源。修改后不得让两处对同一规则产生冲突。
