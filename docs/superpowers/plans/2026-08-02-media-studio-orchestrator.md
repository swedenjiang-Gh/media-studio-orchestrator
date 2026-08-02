# Media Studio Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Create one auto-discoverable Skill that routes local and cloud image, video, audio, and video-learning requests to the verified execution path.

**Architecture:** Create one small router SKILL.md under the personal Codex skills directory and five task-specific references. The router decides scope, health, authorization, execution path, and delivery state; references contain machine paths and detailed gates. Existing specialist Skills and fixed wrappers remain the execution layer.

**Tech Stack:** Codex Agent Skills Markdown, local PowerShell health checks, existing ComfyUI API, existing specialist Skills, skill-creator validation scripts.

## Global Constraints

- Create the final package at C:\Users\J\.codex\skills\media-studio-orchestrator.
- Do not copy models, media, outputs, API keys, tokens, cookies, or user reference assets into the package or repository.
- Do not add a Media MCP, HTTP service, task queue, persistent launcher, or new model download in this implementation.
- Keep SKILL.md under 350 lines; keep detailed rules in references one level below it.
- Preserve user rule: agent API uses the existing hidden local ComfyUI task; manually opened Desktop remains visible.
- Do not submit cloud tasks, invoke GPU generation, or process user media while validating the Skill.

---

### Task 1: Initialize the Skill package

**Files:**
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\SKILL.md
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\agents\openai.yaml
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\references\

**Interfaces:**
- Consumes: skill-creator init_skill.py, the approved design document, display text for the new Skill.
- Produces: a valid, auto-discoverable Skill folder named media-studio-orchestrator.

- [ ] **Step 1: Check that the target folder does not already exist**

Run:

    Test-Path -LiteralPath C:\Users\J\.codex\skills\media-studio-orchestrator

Expected: False. Stop and inspect if True; do not overwrite an existing Skill.

- [ ] **Step 2: Initialize the package with the official generator**

Run the skill-creator init_skill.py script with:

    media-studio-orchestrator
    --path C:\Users\J\.codex\skills
    --resources references
    --interface display_name=Media Studio Orchestrator
    --interface short_description=Route local and cloud media work
    --interface default_prompt=Use my local media studio to handle this task.

Expected: SKILL.md, agents/openai.yaml, and references directory exist.

- [ ] **Step 3: Verify the generated package is intentionally minimal**

Run:

    rg --files C:\Users\J\.codex\skills\media-studio-orchestrator

Expected: only generator files and the references directory. Do not create README, install guide, copied models, or duplicated executable wrappers.

- [ ] **Step 4: Commit the repository plan artifact only**

The personal Skill directory is outside this repository. No repository files change in this task beyond this already committed plan.

### Task 2: Add health, path, and acceptance references

**Files:**
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\references\health-and-paths.md
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\references\acceptance.md

**Interfaces:**
- Consumes: docs/storage-and-credentials.md and docs/validation-and-acceptance.md in the inventory repository.
- Produces: status vocabulary ready, partial, missing, blocked; safe local paths; reproducible acceptance record fields.

- [ ] **Step 1: Write the expected failure scenario**

Scenario: user asks for a local Wan identity-consistent video, but no reference image or validated Canvas/API pair is supplied.

Expected router result: partial, name the required reference image and workflow pair, do not claim video generation or submit a task.

- [ ] **Step 2: Write health-and-paths.md**

Include only the verified locations and checks needed by a future agent:

    ComfyUI API: http://127.0.0.1:8188/object_info
    Comfy shared root: D:\Comfy-Desktop\ComfyUI-Shared
    rembg root: D:\AI\rembg
    video-learning root: D:\CodexVideoLearning
    voice root: D:\AI\Voice
    MuseTalk root: D:\AI\Video\MuseTalk

Require the agent to verify API model dropdowns, CUDA provider, user environment variable, and service ports before calling a dependent chain. State credential locations as existence checks only.

- [ ] **Step 3: Write acceptance.md**

Define the shared output record and material gates for PuLID/Union ControlNet, Wan I2V/T2V, rembg object extraction, video subtitles/translation, face recognition, RVC/GPT-SoVITS, and MuseTalk. Reuse the approved criteria from docs/validation-and-acceptance.md without copying token or asset information.

- [ ] **Step 4: Verify the expected failure scenario**

Read health-and-paths.md and acceptance.md as a fresh executor. Confirm both require reference images and Canvas/API pairs before Wan I2V execution.

Expected: scenario remains partial, not ready.

### Task 3: Add image, video, and audio references

**Files:**
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\references\image.md
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\references\video.md
- Create: C:\Users\J\.codex\skills\media-studio-orchestrator\references\audio.md

**Interfaces:**
- Consumes: current personal specialist Skill rules and health-and-paths.md.
- Produces: deterministic per-domain routing and authorization gates for SKILL.md.

- [ ] **Step 1: Write the image reference**

Define these exclusive paths:

    ordinary semantic image generation or edit -> image_gen
    explicit CLI image request -> Kitool GPT Image
    deterministic pixels -> ImageMagick
    Node project Buffer/Stream -> project-local Sharp after user approval
    semantic person/object cutout -> CUDA rembg
    fixed seed or batch-consistent keyframe -> ComfyUI FLUX

Include FLUX non-commercial, Fill slow, and identity plus pose routing to PuLID plus Union ControlNet.

- [ ] **Step 2: Write the video reference**

Define download, evidence extraction, ASR/OCR/visual cross-check, subtitles, translation, candidate clips, 360 boundaries, ComfyUI Wan, and cloud video rules. Require original subtitles to remain preserved and label unverified translation or speaker attribution. Require the project context package before XYQ, Seedance, or related cloud video submission.

- [ ] **Step 3: Write the audio reference**

Define VoxCPM2 for text-to-speech or one-off authorized reference use, GPT-SoVITS for longer character dataset training, RVC only for speech-to-speech timbre conversion, and MuseTalk for authorized portrait plus driving audio. Require explicit authorization and do not overwrite source output.

- [ ] **Step 4: Verify routing pressure cases**

Evaluate these inputs against all three references:

    Replace a product background but preserve every other pixel.
    Download and summarize a public Japanese tutorial, then create bilingual subtitles.
    Convert an existing narration into an authorized character timbre.

Expected: ImageMagick, download-videos then video-learning, and RVC are selected respectively; each input also receives its relevant authorization and validation gate.

### Task 4: Implement the router SKILL.md and UI metadata

**Files:**
- Modify: C:\Users\J\.codex\skills\media-studio-orchestrator\SKILL.md
- Modify: C:\Users\J\.codex\skills\media-studio-orchestrator\agents\openai.yaml

**Interfaces:**
- Consumes: five reference files from Tasks 2 and 3.
- Produces: the public trigger description and the only mandatory execution order for the orchestration Skill.

- [ ] **Step 1: Write the expected failure scenario**

Scenario: user asks to use Seedance 2.0 mini for a video, but the selected local cloud entry cannot explicitly choose that model.

Expected router result: blocked, explain that model selection cannot be guaranteed, and do not submit.

- [ ] **Step 2: Write the SKILL.md frontmatter**

Use the exact name media-studio-orchestrator. The description starts with Use when and lists the major user phrases that should invoke a unified image, video, audio, subtitle, or media-workflow route. Keep the description focused on trigger conditions rather than restating the process.

- [ ] **Step 3: Write the router body**

Require this order:

    classify request
    read only relevant reference
    run minimum health check
    decide ready/partial/missing/blocked
    enforce authorization and model-selection gates
    select one execution route
    record output and validation boundary

Add a compact decision table, paths to the five references, an explicit statement that the orchestrator does not replace specialist Skills, and a list of prohibited assumptions.

- [ ] **Step 4: Generate or refresh agents/openai.yaml**

Use the skill-creator generator with:

    display_name=Media Studio Orchestrator
    short_description=Route local and cloud media work
    default_prompt=Use my local media studio to handle this task.

- [ ] **Step 5: Verify the expected failure scenario**

Read SKILL.md and video.md. Confirm the Seedance request reaches the model-selection gate and returns blocked without a cloud submission.

Expected: blocked, no request is submitted.

### Task 5: Validate and publish the Skill

**Files:**
- Modify: C:\Users\J\.codex\skills\media-studio-orchestrator\SKILL.md and references only if validation finds a defect.
- Modify: D:\GitHub\codex-local-media-studio\docs\local-media-inventory.md to link the installed Skill and its validation date.

**Interfaces:**
- Consumes: complete Skill package and the four pressure-case outcomes.
- Produces: a validated, installed personal Skill and an updated public inventory record.

- [ ] **Step 1: Run structural validation**

Run the skill-creator quick_validate.py script against C:\Users\J\.codex\skills\media-studio-orchestrator.

Expected: zero validation errors for frontmatter, name, directory, and UI metadata.

- [ ] **Step 2: Run the four no-side-effect pressure cases**

Use the scenarios from Tasks 2, 3, and 4. For each, record selected executor, status, required inputs, and whether any external action was prohibited.

Expected outcomes:

    Wan identity request -> partial
    deterministic background replacement -> ImageMagick
    Japanese tutorial bilingual subtitle request -> download-videos then video-learning, translation marked pending provider validation
    Seedance model request without explicit selector -> blocked

- [ ] **Step 3: Check package boundaries**

Run:

    rg --files C:\Users\J\.codex\skills\media-studio-orchestrator

Then scan for key, token, cookie, model, media, and output artifacts.

Expected: only SKILL.md, agents/openai.yaml, and five Markdown references; no sensitive or binary files.

- [ ] **Step 4: Update inventory and commit**

Add the installed Skill path and validation date to docs/local-media-inventory.md. Stage only that documentation change, run git diff --check and a secret-like literal scan, commit with message Add media studio orchestrator skill, and push main.
