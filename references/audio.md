# Audio and portrait routing

All voice, recording, portrait, and driving-audio work requires explicit authorization. Preserve the supplied source and create a separate output.

| Need | Route | Material gate |
| --- | --- | --- |
| Text narration or one-off authorized reference-voice use | VoxCPM2 | Accurate text and authorized reference audio; confirm its CUDA environment. |
| Long-lived character voice model and GUI/API inference | GPT-SoVITS | Authorized 20–40 minutes of clean single-speaker, no-music/no-reverb recordings plus transcript; train and evaluate a new weight. |
| Keep existing speech content/rhythm but change authorized timbre | RVC | Authorized source speech and target `.pth`; optional matching `.index`. Training requires the same clean dataset gate. |
| Portrait/video plus driving audio lip sync | MuseTalk | Authorized face video or frontal portrait and authorized driving audio; evaluate sync, identity, stability, and drift. |

Do not state that a target voice model exists merely because RVC/GPT-SoVITS base environments are installed. Do not claim a voice clone is approved until authorization and listening review are recorded. MuseTalk does not train a voice model.

Project-owned voice and lip-sync results follow the project directory. Standalone narration/voice conversion uses `D:\MediaStudio\Voice\<job>`; standalone MuseTalk uses `D:\MediaStudio\MuseTalk\<job>`. Keep model weights and runtime environments under their existing `D:\AI` roots. Audio extracted only for video analysis remains inside the owning `video-learning` job.
