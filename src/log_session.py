"""Append research-session rows. Participant ids only, never names."""

import csv
import re
from pathlib import Path

COLUMNS = [
    "session_id",
    "participant_id",
    "task_id",
    "mode",
    "target_photo_id",
    "initial_memory",
    "initial_candidate_count",
    "clarification_1",
    "answer_1",
    "candidate_count_after_1",
    "clarification_2",
    "answer_2",
    "candidate_count_after_2",
    "target_found",
    "time_to_target_seconds",
    "interaction_count",
    "manual_scan_needed",
    "none_of_these_used",
    "undo_used",
    "completed_at",
]


def clean_participant(value):
    text = (value or "").strip().upper()
    if re.fullmatch(r"P\d{2,3}", text):
        return text
    return "P00"


def append_result(path, row):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_header = (not target.exists()) or target.stat().st_size == 0
    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in COLUMNS})


def result_row(state, target_photo_id, completed_at, seconds):
    questions = state["questions"]
    answers = state["answers"]
    counts = state["counts"]
    chosen = state.get("chosen") or ""
    rank = 0
    for index, row in enumerate(state["candidates"], start=1):
        if row["photo_id"] == chosen:
            rank = index
            break
    found = bool(target_photo_id) and chosen == target_photo_id

    def question_text(index):
        if len(questions) > index:
            return questions[index]["text"]
        return ""

    def answer_text(index):
        if len(answers) > index:
            return answers[index]
        return ""

    def count_after(index):
        # counts[0] is the initial set. Later entries follow each answer.
        position = index + 1
        if len(counts) > position:
            return counts[position]
        return ""

    return {
        "session_id": state.get("session_id", ""),
        "participant_id": clean_participant(state.get("participant_id")),
        "task_id": state.get("task_id", ""),
        "mode": state.get("mode", ""),
        "target_photo_id": target_photo_id or "",
        "initial_memory": state.get("memory", ""),
        "initial_candidate_count": counts[0] if counts else "",
        "clarification_1": question_text(0),
        "answer_1": answer_text(0),
        "candidate_count_after_1": count_after(0),
        "clarification_2": question_text(1),
        "answer_2": answer_text(1),
        "candidate_count_after_2": count_after(1),
        "target_found": found,
        "time_to_target_seconds": seconds,
        "interaction_count": state.get("interactions", 0),
        "manual_scan_needed": bool(rank and rank > 3),
        "none_of_these_used": bool(state.get("none_used")),
        "undo_used": bool(state.get("undo_used")),
        "completed_at": completed_at,
    }
