"""Pick one closed question that best splits the current candidates.

Candidate choice is deterministic. Groq may only phrase the chosen clue.
"""

from src.retrieve import normalize
from src.secrets import get_groq_api_key

ATTRIBUTES = (
    "visual_detail",
    "indoors_outdoors",
    "people",
    "month",
    "year",
    "event",
    "location_context",
    "category",
    "association",
)

PRIORITY = {
    "visual_detail": 1.25,
    "indoors_outdoors": 1.15,
    "people": 1.12,
    "month": 1.08,
    "year": 1.05,
    "event": 1.04,
    "location_context": 1.0,
    "category": 0.95,
    "association": 0.9,
}

MIN_BALANCE = 0.2
MAX_MISSING = 0.4


def supplied_attributes(memory, candidates):
    """Attributes whose value the person already said."""
    text = normalize(memory)
    found = set()
    if not text:
        return found
    for attribute in ATTRIBUTES:
        for row in candidates:
            value = normalize(row.get(attribute, ""))
            if value and value in text:
                found.add(attribute)
                break
    if "screenshot" in text:
        found.add("category")
    return found


def choose_discriminator(candidates, supplied, asked):
    """Return the attribute value that best partitions this set."""
    if len(candidates) < 2:
        return None
    best = None
    for attribute in ATTRIBUTES:
        if attribute in supplied or attribute in asked:
            continue
        counts = {}
        missing = 0
        seen = []
        for row in candidates:
            value = (row.get(attribute) or "").strip()
            if not value:
                missing += 1
                continue
            if value not in counts:
                seen.append(value)
            counts[value] = counts.get(value, 0) + 1
        total = len(candidates)
        if missing / total > MAX_MISSING or len(counts) < 2:
            continue
        known = total - missing
        for value in seen:
            count = counts[value]
            other = known - count
            if count < 1 or other < 1:
                continue
            balance = min(count, other) / float(known)
            if balance < MIN_BALANCE:
                continue
            score = balance * (1 - missing / float(total)) * PRIORITY.get(attribute, 1)
            if best is None or score > best["score"]:
                best = {
                    "attribute": attribute,
                    "value": value,
                    "score": score,
                    "matching": count,
                    "others": other,
                }
    return best


def template_question(attribute, value):
    value_text = (value or "").strip()
    if attribute == "indoors_outdoors":
        if value_text == "indoors":
            return "Was this indoors?"
        return "Was this outdoors?"
    if attribute in ("year", "month"):
        return "Was this around {v}?".format(v=value_text)
    if attribute == "people":
        if value_text.lower().startswith("team"):
            return "Was this with {v}?".format(v=value_text)
        if value_text == "solo":
            return "Was this just you?"
        if value_text == "sister":
            return "Was this with your sister?"
        return "Was this with your {v}?".format(v=value_text)
    if attribute == "event":
        return "Was this during the {v}?".format(v=value_text)
    if attribute == "visual_detail":
        if value_text.lower() == "red wall":
            return "Was there a red wall behind you?"
        return "Was there a {v}?".format(v=value_text)
    if attribute == "category" and value_text.lower() == "screenshot":
        return "Was this a screenshot?"
    if attribute == "category":
        return "Was this a {v}?".format(v=value_text)
    if attribute == "location_context":
        return "Was this at a {v}?".format(v=value_text)
    if attribute == "association":
        return "Was this related to {v}?".format(v=value_text)
    return "Was this {v}?".format(v=value_text)


def _acceptable_phrase(text, value):
    cleaned = " ".join((text or "").strip().split())
    if not cleaned or len(cleaned) > 140:
        return False
    if not cleaned.endswith("?"):
        return False
    lowered = cleaned.lower()
    if "tell me more" in lowered or "describe" in lowered:
        return False
    if normalize(value) not in normalize(cleaned):
        return False
    return True


def phrase_question(spec, use_model=True):
    """Natural closed question. Ranking stays outside this function."""
    template = template_question(spec["attribute"], spec["value"])
    if not use_model or not get_groq_api_key():
        return template
    try:
        from groq import Groq

        client = Groq(api_key=get_groq_api_key(), timeout=12)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0.2,
            max_completion_tokens=200,
            reasoning_effort="low",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Rewrite the clue as one short closed question a person could "
                        "answer about their own photo. Keep the clue wording. "
                        "End with a question mark. Do not add facts."
                    ),
                },
                {
                    "role": "user",
                    "content": "Clue: {a} = {v}\nTemplate: {t}".format(
                        a=spec["attribute"], v=spec["value"], t=template
                    ),
                },
            ],
        )
        text = (response.choices[0].message.content or "").strip().splitlines()[0]
    except Exception:
        return template
    if _acceptable_phrase(text, spec["value"]):
        return " ".join(text.split())
    return template
