#!/usr/bin/env python3
"""Export Lightroom Classic person labels and image metadata without modifying the catalog."""

import argparse
import csv
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path


OUTPUT_FILES = ("people-summary.csv", "people-photos.csv", "people-faces.csv", "README.md")

PEOPLE_SQL = """
with valid_faces as (
  select kf.tag as keyword_id, f.id_local as face_id, f.image as image_id,
         coalesce(kf.userPick, 0) as user_pick,
         f.tl_x, f.tl_y, f.tr_x, f.tr_y, f.br_x, f.br_y, f.bl_x, f.bl_y
  from AgLibraryKeywordFace kf
  join AgLibraryFace f on f.id_local = kf.face
  where coalesce(kf.userReject, 0) = 0
    and coalesce(f.ignored, 0) = 0
),
image_people as (
  select vf.image_id, group_concat(kw.name, ' | ') as people_in_photo
  from valid_faces vf
  join AgLibraryKeyword kw on kw.id_local = vf.keyword_id
  where kw.keywordType = 'person'
  group by vf.image_id
)
select kw.id_local as person_id, kw.name as person,
       vf.face_id, vf.image_id, vf.user_pick,
       vf.tl_x, vf.tl_y, vf.tr_x, vf.tr_y, vf.br_x, vf.br_y, vf.bl_x, vf.bl_y,
       ai.captureTime, ai.originalCaptureTime, ai.fileWidth, ai.fileHeight,
       ai.fileFormat, ai.rating, ai.pick, ai.colorLabels,
       rf.absolutePath as root_path, fo.pathFromRoot as folder_path,
       fi.idx_filename as filename, fi.extension, ip.people_in_photo
from AgLibraryKeyword kw
left join valid_faces vf on vf.keyword_id = kw.id_local
left join Adobe_images ai on ai.id_local = vf.image_id
left join AgLibraryFile fi on fi.id_local = ai.rootFile
left join AgLibraryFolder fo on fo.id_local = fi.folder
left join AgLibraryRootFolder rf on rf.id_local = fo.rootFolder
left join image_people ip on ip.image_id = vf.image_id
where kw.keywordType = 'person'
order by lower(kw.name), ai.captureTime, fi.idx_filename, vf.face_id
"""


def catalog_uri(catalog: Path) -> str:
    return f"file:{catalog.resolve().as_posix()}?mode=ro"


def image_path(root_path, folder_path, filename) -> str:
    if not root_path or not filename:
        return ""
    return str(Path(root_path) / (folder_path or "") / filename)


def write_csv(path: Path, fields, rows) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export(catalog: Path, output_dir: Path) -> dict:
    if not catalog.is_file():
        raise FileNotFoundError(f"Lightroom catalog not found: {catalog}")
    output_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(catalog_uri(catalog), uri=True)
    connection.row_factory = sqlite3.Row
    try:
        records = [dict(row) for row in connection.execute(PEOPLE_SQL)]
    finally:
        connection.close()

    photos = {}
    people = defaultdict(lambda: {"faces": 0, "photos": set(), "dates": [], "roots": set()})
    face_rows = []
    for row in records:
        person = row["person"]
        info = people[person]
        if row["face_id"] is None:
            continue
        path = image_path(row["root_path"], row["folder_path"], row["filename"])
        row["photo_path"] = path
        face_rows.append(row)
        info["faces"] += 1
        info["photos"].add(row["image_id"])
        if row["captureTime"]:
            info["dates"].append(row["captureTime"])
        if row["root_path"]:
            info["roots"].add(row["root_path"])
        photo_key = (person, row["image_id"])
        existing = photos.get(photo_key)
        if existing is None:
            existing = dict(row)
            existing["face_count_for_person"] = 0
            existing["picked_face_count_for_person"] = 0
            photos[photo_key] = existing
        existing["face_count_for_person"] += 1
        existing["picked_face_count_for_person"] += int(row["user_pick"] or 0)

    summary_rows = []
    for person in sorted(people, key=str.casefold):
        info = people[person]
        summary_rows.append({
            "person": person,
            "valid_face_count": info["faces"],
            "unique_photo_count": len(info["photos"]),
            "first_capture_time": min(info["dates"], default=""),
            "last_capture_time": max(info["dates"], default=""),
            "root_paths": " | ".join(sorted(info["roots"], key=str.casefold)),
        })

    photo_fields = [
        "person", "image_id", "photo_path", "captureTime", "originalCaptureTime",
        "fileWidth", "fileHeight", "fileFormat", "extension", "rating", "pick",
        "colorLabels", "people_in_photo", "face_count_for_person", "picked_face_count_for_person",
    ]
    face_fields = [
        "person", "face_id", "image_id", "photo_path", "captureTime", "fileWidth", "fileHeight",
        "user_pick", "tl_x", "tl_y", "tr_x", "tr_y", "br_x", "br_y", "bl_x", "bl_y",
        "people_in_photo",
    ]
    write_csv(output_dir / "people-summary.csv", list(summary_rows[0]) if summary_rows else [
        "person", "valid_face_count", "unique_photo_count", "first_capture_time", "last_capture_time", "root_paths",
    ], summary_rows)
    write_csv(output_dir / "people-photos.csv", photo_fields, sorted(photos.values(), key=lambda r: (r["person"].casefold(), r["captureTime"] or "", r["photo_path"])))
    write_csv(output_dir / "people-faces.csv", face_fields, face_rows)

    total_faces = sum(item["valid_face_count"] for item in summary_rows)
    total_photos = len({row["image_id"] for row in face_rows})
    missing_paths = len({
        row["image_id"] for row in face_rows
        if not row["photo_path"] or not Path(row["photo_path"]).is_file()
    })
    report = [
        "# Lightroom 人物索引",
        "",
        f"- Catalog: `{catalog}`",
        f"- Exported: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        f"- Person labels: {len(summary_rows)}",
        f"- Valid face boxes: {total_faces}",
        f"- Unique tagged photos: {total_photos}",
        f"- Missing/unavailable tagged photos: {missing_paths}",
        "",
        "Only Lightroom faces not marked rejected or ignored are included. The catalog was opened with SQLite read-only mode.",
        "",
        "## Files",
        "",
        "- `people-summary.csv`: one row per Lightroom person label.",
        "- `people-photos.csv`: one row per person/photo, with metadata and same-photo people labels.",
        "- `people-faces.csv`: one row per valid face, including normalized Lightroom face quadrilateral coordinates.",
    ]
    (output_dir / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return {"people": len(summary_rows), "faces": total_faces, "photos": total_photos, "missing_paths": missing_paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = export(args.catalog, args.output)
    print("Exported {people} people, {faces} valid faces, {photos} photos; {missing_paths} photo paths unavailable.".format(**result))


if __name__ == "__main__":
    main()
