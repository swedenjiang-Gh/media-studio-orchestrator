#!/usr/bin/env python3
"""Rename Insta360 video files to days-offset + sequence format.

Groups by recording moment (same datetime + sequence), renames all related files
(.insv, .lrv, .mp4, .insp, .bin sidecars) to a shared xxx_yyy prefix.
Images (.jpg, .dng, .png) are left untouched.
"""

import os
import re
import csv
from datetime import datetime, date
from itertools import groupby
from collections import defaultdict


VID_PAT = re.compile(r"^(VID|LRV|IMG)_(\d{8}_\d{6})_(\d{2})_(\d{3})\.(.+)$", re.I)
BIN_PAT = re.compile(r"^(LRV|VID)_(\d{8}_\d{6})_(\d{2})_(\d{3})\.(lrv|insv)\.(.+)\.bin$", re.I)
IMG_EXTS = {".jpg", ".jpeg", ".png", ".dng", ".bmp", ".gif", ".heic", ".heif", ".tiff"}
VID_EXTS = {".insv", ".lrv", ".mp4", ".insp"}


def group_key(datetime_str: str, seq: str) -> str:
    return f"{datetime_str}_{seq}"


def parse_video(filename: str):
    m = VID_PAT.match(filename)
    if not m:
        return None
    return group_key(m.group(2), m.group(4)), datetime.strptime(m.group(2), "%Y%m%d_%H%M%S")


def parse_bin(filename: str):
    m = BIN_PAT.match(filename)
    if not m:
        return None
    return group_key(m.group(2), m.group(4)), datetime.strptime(m.group(2), "%Y%m%d_%H%M%S")


def build_mapping(target_dir: str, ref_date: date) -> list[tuple[str, str]]:
    all_files = [
        f for f in os.listdir(target_dir)
        if os.path.isfile(os.path.join(target_dir, f))
    ]

    # Separate candidates
    videos = [
        f for f in all_files
        if os.path.splitext(f)[1].lower() in VID_EXTS
    ]
    bins = [
        f for f in all_files
        if f.lower().endswith(".bin")
    ]

    # Group recordings by datetime+seq
    rec_map: dict[str, dict] = {}  # gkey -> {files, dt}

    for f in videos:
        r = parse_video(f)
        if r is None:
            continue
        gkey, dt = r
        if gkey not in rec_map:
            rec_map[gkey] = {"files": [], "dt": dt}
        rec_map[gkey]["files"].append(f)

    for f in bins:
        r = parse_bin(f)
        if r is None:
            continue
        gkey, dt = r
        if gkey not in rec_map:
            rec_map[gkey] = {"files": [], "dt": dt}
        rec_map[gkey]["files"].append(f)

    # Sort items by datetime, then group by day offset
    items = sorted(rec_map.items(), key=lambda x: x[1]["dt"])

    def days_of(item):
        return (item[1]["dt"].date() - ref_date).days

    mapping = []
    for days, grp in groupby(items, key=days_of):
        glist = sorted(grp, key=lambda x: x[1]["dt"])
        for seq, (gkey, info) in enumerate(glist, 1):
            prefix = f"{days}_{seq:03d}"
            for old_name in info["files"]:
                # Build new name
                old_lower = old_name.lower()
                if old_lower.endswith(".bin"):
                    # VID/LRV_DATE_XX_YYY.xxx.bin -> prefix.xxx.bin (keep original case)
                    idx = old_name.lower().find(".")  # first dot after prefix
                    if idx > 0:
                        rest = old_name[idx + 1:]  # lrv.xxx.bin or insv.xxx.bin
                    else:
                        rest = old_name
                    new_name = f"{prefix}.{rest}"
                else:
                    # VID/LRV/IMG_DATE_XX_YYY.ext -> prefix.ext
                    m = re.match(
                        r"^(VID|LRV|IMG)_"
                        + re.escape(gkey[:15])
                        + r"_\d{2}_"
                        + re.escape(gkey[16:])
                        + r"\.(.+)$",
                        old_name,
                        re.I,
                    )
                    if m:
                        new_name = f"{prefix}.{m.group(6).lower()}"
                    else:
                        new_name = old_name  # shouldn't happen

                mapping.append((old_name, new_name))

    return mapping


def save_backup(mapping: list[tuple[str, str]], backup_path: str):
    with open(backup_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["old_name", "new_name"])
        for old, new in mapping:
            writer.writerow([old, new])


def rename_files(target_dir: str, mapping: list[tuple[str, str]]):
    count = 0
    for old, new in mapping:
        old_path = os.path.join(target_dir, old)
        new_path = os.path.join(target_dir, new)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            count += 1
        else:
            print(f"  [MISSING] {old}")
    return count


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Rename Insta360 video files to days-offset + sequence format"
    )
    parser.add_argument(
        "target",
        help="Target directory containing Insta360 files",
    )
    parser.add_argument(
        "--ref-date",
        default="2024-12-10",
        help="Reference date for day offset calculation (YYYY-MM-DD, default: 2024-12-10)",
    )
    parser.add_argument(
        "--backup",
        default=None,
        help="Backup CSV output path (default: <target>/rename_backup.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview only, do not rename",
    )
    args = parser.parse_args()

    target_dir = args.target
    ref_date = datetime.strptime(args.ref_date, "%Y-%m-%d").date()
    backup_path = args.backup or os.path.join(target_dir, "rename_backup.csv")

    mapping = build_mapping(target_dir, ref_date)

    if not mapping:
        print("No Insta360 video files found.")
        return

    # Print summary
    groups = defaultdict(list)
    for old, new in mapping:
        prefix = new.split(".")[0]
        groups[prefix].append(old)

    print(f"Target: {target_dir}")
    print(f"Reference date: {args.ref_date}")
    print(f"Files to rename: {len(mapping)}")
    print(f"Recording groups: {len(groups)}")
    print(f"Max files per group: {max(len(v) for v in groups.values())}")
    print()

    if args.dry_run:
        print("=== DRY RUN (preview) ===")
        # Show first 5 groups
        shown = 0
        for prefix in sorted(groups.keys(), key=lambda x: (int(x.split("_")[0]), int(x.split("_")[1]))):
            old_files = groups[prefix]
            print(f"\n{prefix} ({len(old_files)} files):")
            for o in old_files:
                new = next(n for old_n, n in mapping if old_n == o)
                print(f"  {o}  ->  {new}")
            shown += 1
            if shown >= 5:
                break
        remaining = len(groups) - shown
        if remaining > 0:
            print(f"\n... and {remaining} more groups")
        print(f"\nTotal: {len(mapping)} files in {len(groups)} groups (DRY RUN - no changes made)")
    else:
        save_backup(mapping, backup_path)
        print(f"Backup saved: {backup_path}")
        count = rename_files(target_dir, mapping)
        print(f"\nDone. {count} files renamed.")


if __name__ == "__main__":
    main()
