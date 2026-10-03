"""Logic tests for the photo MVP. Run from the repository root:

    python mvp/tests/test_flow.py
"""

import csv
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.flow import answer, groups, new_state, none_of_these, start_search, undo
from src.library import load_library, load_tasks
from src.log_session import COLUMNS, append_result, clean_participant, result_row
from src.question import phrase_question, template_question
from src.retrieve import normalize

EXPECTED_QUESTION = {
    "TASK01": "red wall",
    "TASK02": "ceremony",
    "TASK03": "team a",
    "TASK04": "march",
    "TASK05": "classmates",
    "TASK06": "indoors",
}


def ids(state):
    return [row["photo_id"] for row in state["candidates"]]


def scores(state):
    return [row["score"] for row in state["candidates"]]


def run():
    library = load_library()
    tasks = load_tasks()
    assert len(library) == 40, len(library)
    assert len(tasks) >= 6
    clusters = {}
    for row in library:
        clusters.setdefault(row["test_target"] or row["event"], 0)
    assert sum(1 for row in library if row["event"] == "birthday") >= 6
    for task in tasks:
        hidden = task["hidden_discriminator"].split(":", 1)[1]
        assert hidden.lower() not in task["memory_prompt"].lower()
        state = new_state()
        start_search(state, task["memory_prompt"], library, use_model=False)
        found = ids(state)
        assert task["target_photo_id"] in found, (task["task_id"], found)
        assert 6 <= len(found) <= 10, (task["task_id"], len(found))
        assert state["pending"], task["task_id"]
        assert "tell me more" not in state["pending"]["text"].lower()
        assert EXPECTED_QUESTION[task["task_id"]] in state["pending"]["text"].lower()
        for row in state["candidates"]:
            assert Path(row["image_file"]).is_file()

    birthday = new_state()
    start_search(birthday, "birthday with school friends", library, use_model=False)
    before_ids = ids(birthday)
    before_scores = scores(birthday)
    answer(birthday, "not_sure", use_model=False)
    assert scores(birthday) == before_scores
    assert ids(birthday) == before_ids
    assert birthday["pending"]["attribute"] == "month"

    start_search(birthday, "birthday with school friends", library, use_model=False)
    first = birthday["pending"]["text"]
    answer(birthday, "yes", use_model=False)
    strong, rest = groups(birthday)
    assert "Narrowed from" in birthday["message"]
    assert len(strong) < len(before_ids)
    assert "P01" in [row["photo_id"] for row in strong]
    assert birthday["pending"]
    assert birthday["pending"]["text"] != first
    answer(birthday, "yes", use_model=False)
    assert birthday["pending"] is None
    assert len(birthday["questions"]) == 2
    strong_ids = [row["photo_id"] for row in groups(birthday)[0]]
    assert strong_ids == ["P01", "P02"]
    answer(birthday, "yes", use_model=False)
    assert len(birthday["questions"]) == 2

    start_search(birthday, "birthday with school friends", library, use_model=False)
    initial_order = ids(birthday)
    initial_scores = scores(birthday)
    answer(birthday, "yes", use_model=False)
    answer(birthday, "yes", use_model=False)
    assert scores(birthday) != initial_scores
    undo(birthday)
    assert len(birthday["questions"]) == 1
    assert birthday["pending"]
    undo(birthday)
    assert ids(birthday) == initial_order
    assert scores(birthday) == initial_scores
    assert birthday["undo_used"]

    start_search(birthday, "birthday with school friends", library, use_model=False)
    original = set(ids(birthday))
    none_of_these(birthday)
    assert set(ids(birthday)) - original
    assert original.issubset(set(ids(birthday)))
    undo(birthday)
    assert set(ids(birthday)) == original

    wrong = new_state()
    start_search(wrong, "birthday with school friends", library, use_model=False)
    answer(wrong, "no", use_model=False)
    assert "P01" in ids(wrong)

    baseline = new_state()
    start_search(baseline, "football match with my team", library, mode="baseline", use_model=False)
    assert baseline["pending"] is None
    mvp = new_state()
    start_search(mvp, "football match with my team", library, mode="mvp", use_model=False)
    assert mvp["pending"]
    assert "P08" in ids(mvp)

    spec = {"attribute": "visual_detail", "value": "red wall"}
    assert phrase_question(spec, use_model=False) == template_question("visual_detail", "red wall")
    import src.question as question_module

    original_key = question_module.get_groq_api_key
    question_module.get_groq_api_key = lambda: "present"
    fake = types.ModuleType("groq")

    class Broken:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("unavailable")

    fake.Groq = Broken
    sys.modules["groq"] = fake
    try:
        assert phrase_question(spec, use_model=True) == template_question("visual_detail", "red wall")
    finally:
        question_module.get_groq_api_key = original_key

    assert clean_participant("P01") == "P01"
    assert clean_participant("someone") == "P00"
    logged = new_state()
    start_search(logged, "screenshot of my sales targets", library, use_model=False, test_mode=True)
    logged["participant_id"] = "someone"
    logged["task_id"] = "TASK04"
    answer(logged, "yes", use_model=False)
    logged["chosen"] = "P22"
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "test_results.csv"
        row = result_row(logged, "P22", "2026-10-03T00:00:00+00:00", 3.2)
        append_result(path, row)
        with path.open(encoding="utf-8", newline="") as handle:
            saved = list(csv.DictReader(handle))
        assert list(saved[0].keys()) == COLUMNS
        assert saved[0]["participant_id"] == "P00"
        assert saved[0]["target_found"] == "True"
        assert saved[0]["clarification_1"]
        assert "name" not in COLUMNS

    print("passed", len(tasks), "tasks", len(library), "photos")


if __name__ == "__main__":
    run()
