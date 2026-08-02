---
name: download-videos
description: Use when the user provides a Bilibili, YouTube, Douyin, X/Twitter, or other supported video URL and explicitly asks to download, save, fetch, or extract it locally. Route Bilibili links through BBDown and other links through the existing D-drive yt-dlp environment.
---

Run `scripts/download-video.ps1` with `pwsh.exe -File`; pass the URL and, unless the user specifies otherwise, use `D:\VideoDownloads`.

Use the script's fixed paths. Do not invoke a bare `yt-dlp` command.

For Bilibili and b23.tv links, let the script use BBDown. For YouTube, Douyin, X/Twitter, and other supported links, let it use yt-dlp.

Download only content the user is entitled to save. Do not bypass DRM, payment, or access controls. In this user's video-learning workflow, a request to learn a supplied video counts as explicit authorization to save its accessible local copy; do not ask a second download-confirmation question. If yt-dlp requires login cookies, use only the already configured private cookie source that the fixed script passes to yt-dlp's `--cookies` argument. Do not inspect, print, export, copy, commit, or otherwise expose cookie contents. A report that the session has rotated or expired is an authentication-state warning, not permission to bypass access controls; refresh it only when the accessible download is actually blocked.

After completion, report the saved file path. If the request is to learn the video, continue with `video-learning` instead of stopping at the download result. For a batch of user-supplied links, continue through every accessible item and return only the final combined learning results plus blocked or partial items. Do not download merely because a link was mentioned; require an explicit download request or a request to learn that specific video.
