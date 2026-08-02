# `.agents` 小云雀 Skill 快照

这两个 Skill 的来源是 `%USERPROFILE%\.agents\skills\`，不是 Codex 的 `%USERPROFILE%\.codex\skills\`。它们带有 `user-invocable` 和 OpenClaw metadata，因此不能使用 Codex `quick_validate.py` 校验；保留原格式才能在其原生运行时被发现。

- `xyq-skill`：小云雀图像、视频和编辑会话。
- `xyq-short-drama-skill`：小云雀短剧场景。

安装时复制回 `%USERPROFILE%\.agents\skills\`。所有云端视频提交仍须由 `media-studio-orchestrator` 路由，并先准备任务上下文包。
