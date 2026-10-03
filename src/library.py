"""Load the controlled demo library. Paths are relative to the mvp folder."""

import csv
from pathlib import Path

MVP_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = MVP_ROOT / "data" / "photo_library.csv"
TASKS_PATH = MVP_ROOT / "data" / "test_tasks.csv"
RESULTS_PATH = MVP_ROOT / "data" / "test_results.csv"

LIBRARY_FIELDS = [
    "photo_id",
    "image_path",
    "year",
    "month",
    "people",
    "event",
    "location_context",
    "indoors_outdoors",
    "visual_detail",
    "category",
    "association",
    "description",
    "search_text",
    "test_target",
]


def load_library(path=None):
    target = Path(path) if path else LIBRARY_PATH
    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["image_file"] = (MVP_ROOT / row["image_path"]).resolve()
    return rows


def load_tasks(path=None):
    target = Path(path) if path else TASKS_PATH
    with target.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
