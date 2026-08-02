---
name: insta360-rename
description: Batch rename Insta360 camera video files (.insv .lrv .mp4 .insp) and their metadata sidecars (.bin) to a compact days-offset + sequence format. Preserves recording-moment grouping so paired dual-lens files and bins share the same prefix. Use when the user wants to rename, reorganize, or standardize Insta360 footage filenames, especially in directories like "F:\Insta360" or similar.
---

# Insta360 Rename

Renames Insta360 video files using `scripts/rename.py`.

## What It Does

- Groups files by recording moment (same datetime + sequence number), ignoring lens ID
- Calculates day offset from a reference date (default `2024-12-10`)
- Assigns same `{days}_{seq}` prefix to all files of the same recording
- Handles `.insv`, `.lrv`, `.mp4`, `.insp` video files and `.bin` metadata sidecars
- Skips image files (`.jpg`, `.dng`, `.png`, etc.)
- Generates a backup CSV before renaming

## Usage

```bash
# Preview (dry-run)
python scripts/rename.py "F:\Insta360" --dry-run

# Execute with default reference date (2024-12-10)
python scripts/rename.py "F:\Insta360"

# Custom reference date and backup path
python scripts/rename.py "F:\Insta360" --ref-date 2025-01-01 --backup "D:\backup.csv"
```

## Workflow

1. Ask the user for the target directory and reference date
2. Run `--dry-run` first and show the user a preview (first few groups)
3. Wait for confirmation before executing
4. After renaming, confirm the result
5. Remind the user that the backup CSV can be used with a reverse script to restore original names if needed
