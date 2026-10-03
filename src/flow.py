"""Search, one or two closed questions, rerank, undo, and widen."""

import copy
import time
import uuid

from src.question import choose_discriminator, phrase_question, supplied_attributes
from src.retrieve import initial_candidates, normalize, rank_library

MAX_QUESTIONS = 2


def new_state():
    return {
        "session_id": uuid.uuid4().hex[:12],
        "started": False,
        "memory": "",
        "mode": "mvp",
        "candidates": [],
        "universe": [],
        "questions": [],
        "answers": [],
        "pending": None,
        "counts": [],
        "message": "",
        "chosen": None,
        "none_used": False,
        "undo_used": False,
        "interactions": 0,
        "t0": None,
        "task_id": "",
        "participant_id": "P01",
        "test_mode": False,
        "logged": False,
        "history": [],
    }


def _asked(state):
    return {item["attribute"] for item in state["questions"]}


def _sort(rows):
    rows.sort(key=lambda item: (-item["score"], item["photo_id"]))
    return rows


def refresh_question(state, use_model=True):
    if state["mode"] != "mvp" or len(state["questions"]) >= MAX_QUESTIONS:
        state["pending"] = None
        return None
    supplied = supplied_attributes(state["memory"], state["candidates"])
    asked = _asked(state)
    pool = _focus(state)
    spec = choose_discriminator(pool, supplied, asked)
    if spec is None and pool is not state["candidates"]:
        spec = choose_discriminator(state["candidates"], supplied, asked)
    if spec is None:
        state["pending"] = None
        return None
    spec = dict(spec)
    spec["text"] = phrase_question(spec, use_model=use_model)
    state["pending"] = spec
    return spec


def _focus(state):
    """After a yes/no, question the photos still consistent with that answer."""
    if not state["answers"]:
        return state["candidates"]
    if state["answers"][-1] not in ("yes", "no"):
        return state["candidates"]
    strong, _rest = groups(state)
    if len(strong) >= 2:
        return strong
    return state["candidates"]


def groups(state):
    constraints = [
        (question, choice)
        for question, choice in zip(state["questions"], state["answers"])
        if choice in ("yes", "no")
    ]
    if not constraints:
        return list(state["candidates"]), []
    strong = []
    rest = []
    for row in state["candidates"]:
        consistent = True
        for question, choice in constraints:
            matches = normalize(row.get(question["attribute"])) == normalize(question["value"])
            if choice == "yes" and not matches:
                consistent = False
            if choice == "no" and matches:
                consistent = False
        if consistent:
            strong.append(row)
        else:
            rest.append(row)
    return strong, rest


def start_search(state, memory, library, mode="mvp", use_model=True, test_mode=False):
    state["started"] = True
    state["memory"] = (memory or "").strip()
    state["mode"] = mode if mode in ("mvp", "baseline") else "mvp"
    state["candidates"] = initial_candidates(state["memory"], library)
    state["universe"] = rank_library(state["memory"], library)
    state["questions"] = []
    state["answers"] = []
    state["history"] = []
    state["chosen"] = None
    state["logged"] = False
    state["none_used"] = False
    state["undo_used"] = False
    state["interactions"] = 1
    state["counts"] = [len(state["candidates"])]
    if test_mode:
        state["test_mode"] = True
        state["t0"] = time.time()
    else:
        state["t0"] = None
    if not state["candidates"]:
        state["message"] = "No close matches in the demo library."
        state["pending"] = None
        return state
    state["message"] = "I found some possible matches."
    if state["mode"] == "baseline":
        state["pending"] = None
    else:
        refresh_question(state, use_model=use_model)
        if state["pending"] is None:
            state["message"] = "I don't have a useful question yet — here are the closest matches."
    return state


def _snapshot(state):
    return {
        "candidates": copy.deepcopy(state["candidates"]),
        "questions": copy.deepcopy(state["questions"]),
        "answers": list(state["answers"]),
        "pending": copy.deepcopy(state["pending"]),
        "counts": list(state["counts"]),
        "message": state["message"],
        "chosen": state["chosen"],
    }


def answer(state, choice, use_model=True):
    pending = state.get("pending")
    if not pending or len(state["questions"]) >= MAX_QUESTIONS:
        return state
    choice = (choice or "").strip().lower().replace(" ", "_")
    if choice not in ("yes", "no", "not_sure"):
        return state
    state["history"].append(_snapshot(state))
    state["questions"].append(
        {
            "attribute": pending["attribute"],
            "value": pending["value"],
            "text": pending["text"],
        }
    )
    state["answers"].append(choice)
    state["interactions"] += 1
    previous = state["counts"][-1] if state["counts"] else len(state["candidates"])
    if choice in ("yes", "no"):
        for row in state["candidates"]:
            matches = normalize(row.get(pending["attribute"])) == normalize(pending["value"])
            if choice == "yes":
                row["score"] *= 2.5 if matches else 0.5
            else:
                row["score"] *= 0.45 if matches else 2.2
        _sort(state["candidates"])
        strong, _rest = groups(state)
        after = len(strong)
        if after < previous:
            state["message"] = "Narrowed from {b} possible photos to {a}.".format(b=previous, a=after)
            state["counts"].append(after)
        else:
            state["message"] = "I found some possible matches."
            state["counts"].append(previous)
    else:
        state["message"] = "One more detail could help."
        state["counts"].append(previous)
    refresh_question(state, use_model=use_model)
    if state["pending"] is None and len(state["questions"]) >= MAX_QUESTIONS and "Narrowed" not in state["message"]:
        state["message"] = "Here are the closest matches."
    return state


def undo(state):
    if not state["history"]:
        return state
    snap = state["history"].pop()
    state["undo_used"] = True
    state["interactions"] += 1
    for key in ("candidates", "questions", "answers", "pending", "counts", "message", "chosen"):
        state[key] = snap[key]
    state["logged"] = False
    return state


def none_of_these(state):
    state["history"].append(_snapshot(state))
    state["none_used"] = True
    state["interactions"] += 1
    have = {row["photo_id"] for row in state["candidates"]}
    extras = []
    for row in state["universe"]:
        if row["photo_id"] in have:
            continue
        extras.append(dict(row))
        if len(extras) >= 6:
            break
    if not extras:
        state["message"] = "These are all the photos in the demo library."
        return state
    state["candidates"].extend(extras)
    _sort(state["candidates"])
    state["message"] = "Here are more photos from the demo library."
    state["counts"].append(len(state["candidates"]))
    refresh_question(state, use_model=False)
    return state


def select_photo(state, photo_id):
    state["chosen"] = photo_id
    state["interactions"] += 1
    return state


def elapsed_seconds(state):
    if not state.get("t0"):
        return ""
    return round(time.time() - state["t0"], 1)
