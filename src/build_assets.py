"""Write the demo library CSV and local placeholder images.

Run from the repository root:

    python mvp/src/build_assets.py
"""

import csv
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.library import LIBRARY_FIELDS, LIBRARY_PATH, RESULTS_PATH, TASKS_PATH
from src.log_session import COLUMNS

# 5x7 glyphs. Each row is five bits, left to right.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def photo(**kwargs):
    row = {field: "" for field in LIBRARY_FIELDS}
    row.update(kwargs)
    row["image_path"] = "assets/photos/{pid}.png".format(pid=row["photo_id"])
    return row


def catalog():
    rows = []
    birthday = [
        ("P01", "red wall", "June", "TASK01"),
        ("P02", "red wall", "June", ""),
        ("P03", "red wall", "July", ""),
        ("P04", "blue wall", "June", ""),
        ("P05", "blue wall", "July", ""),
        ("P06", "blue wall", "July", ""),
    ]
    for pid, visual, month, target in birthday:
        rows.append(photo(
            photo_id=pid, year="2021", month=month, people="school friends",
            event="birthday", location_context="restaurant", indoors_outdoors="indoors",
            visual_detail=visual, category="photo", association="school",
            description="School friends at a birthday dinner with a {v}.".format(v=visual),
            search_text="birthday school friends restaurant", test_target=target,
        ))
    rows.append(photo(
        photo_id="P07", year="2022", month="April", people="family", event="birthday",
        location_context="home", indoors_outdoors="indoors", visual_detail="cake",
        category="photo", association="family",
        description="A family birthday cake at home.",
        search_text="birthday family home cake",
    ))

    matches = [
        ("P08", "Team A", "crowd", "TASK03"),
        ("P09", "Team A", "crowd", ""),
        ("P10", "Team A", "goalposts", ""),
        ("P11", "Team B", "crowd", ""),
        ("P12", "Team B", "crowd", ""),
        ("P13", "Team B", "crowd", ""),
    ]
    for pid, people, visual, target in matches:
        rows.append(photo(
            photo_id=pid, year="2022", month="October", people=people, event="football match",
            location_context="stadium", indoors_outdoors="outdoors", visual_detail=visual,
            category="photo", association="club",
            description="{p} during a football match.".format(p=people),
            search_text="football match team stadium", test_target=target,
        ))
    rows.append(photo(
        photo_id="P14", year="2021", month="May", people="Team A", event="football training",
        location_context="training ground", indoors_outdoors="outdoors", visual_detail="cones",
        category="photo", association="club",
        description="Team A at football training.",
        search_text="football training team",
    ))

    wedding = [
        ("P15", "wedding ceremony", "white dress", "photo", "TASK02"),
        ("P16", "wedding ceremony", "flowers", "photo", ""),
        ("P17", "wedding ceremony", "aisle", "photo", ""),
        ("P18", "wedding invitation", "invitation card", "screenshot", ""),
        ("P19", "wedding invitation", "invitation card", "screenshot", ""),
        ("P20", "wedding group", "family group", "photo", ""),
    ]
    for pid, event, visual, category, target in wedding:
        rows.append(photo(
            photo_id=pid, year="2021", month="August", people="sister", event=event,
            location_context="family home", indoors_outdoors="indoors", visual_detail=visual,
            category=category, association="sister",
            description="Sister's {e}.".format(e=event),
            search_text="sister wedding family", test_target=target,
        ))
    rows.append(photo(
        photo_id="P21", year="2019", month="September", people="friends", event="wedding ceremony",
        location_context="garden", indoors_outdoors="outdoors", visual_detail="arch",
        category="photo", association="friends",
        description="Friends at an outdoor wedding.",
        search_text="wedding friends garden",
    ))

    sales = [
        ("P22", "March", "TASK04"),
        ("P23", "March", ""),
        ("P24", "March", ""),
        ("P25", "September", ""),
        ("P26", "September", ""),
        ("P27", "September", ""),
    ]
    for pid, month, target in sales:
        rows.append(photo(
            photo_id=pid, year="2023", month=month, people="", event="sales review",
            location_context="phone", indoors_outdoors="", visual_detail="sales chart",
            category="screenshot", association="work",
            description="Screenshot of sales targets from {m}.".format(m=month),
            search_text="screenshot sales targets", test_target=target,
        ))
    rows.append(photo(
        photo_id="P28", year="2022", month="January", people="", event="message",
        location_context="phone", indoors_outdoors="", visual_detail="chat thread",
        category="screenshot", association="work",
        description="A screenshot of a message thread.",
        search_text="screenshot message",
    ))

    graduation = [
        ("P29", "classmates", "TASK05"),
        ("P30", "classmates", ""),
        ("P31", "classmates", ""),
        ("P32", "family", ""),
        ("P33", "family", ""),
        ("P34", "solo", ""),
    ]
    for pid, people, target in graduation:
        rows.append(photo(
            photo_id=pid, year="2022", month="June", people=people, event="graduation ceremony",
            location_context="campus", indoors_outdoors="outdoors", visual_detail="cap and gown",
            category="photo", association="school",
            description="Graduation photo with {p}.".format(p=people),
            search_text="graduation ceremony campus", test_target=target,
        ))

    meals = [
        ("P35", "dinner", "indoors", "restaurant", "TASK06"),
        ("P36", "dinner", "indoors", "restaurant", ""),
        ("P37", "dinner", "indoors", "restaurant", ""),
        ("P38", "picnic", "outdoors", "beach", ""),
        ("P39", "picnic", "outdoors", "beach", ""),
        ("P40", "picnic", "outdoors", "beach", ""),
    ]
    for pid, event, setting, place, target in meals:
        rows.append(photo(
            photo_id=pid, year="2021", month="July", people="friends", event=event,
            location_context=place, indoors_outdoors=setting, visual_detail="shared table",
            category="photo", association="travel",
            description="A {e} with friends during a trip.".format(e=event),
            search_text="meal friends trip", test_target=target,
        ))
    return rows


TASKS = [
    ("TASK01", "P01", "birthday with school friends", "medium", "birthday", "visual_detail:red wall"),
    ("TASK02", "P15", "my sister's wedding", "medium", "wedding", "event:wedding ceremony"),
    ("TASK03", "P08", "football match with my team", "medium", "football", "people:Team A"),
    ("TASK04", "P22", "screenshot of my sales targets", "medium", "screenshot", "month:March"),
    ("TASK05", "P29", "my graduation photo", "easy", "graduation", "people:classmates"),
    ("TASK06", "P35", "a meal with friends on a trip", "hard", "travel", "indoors_outdoors:indoors"),
]


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path, width, height, pixels):
    raw = b"".join(b"\x00" + bytes(row) for row in pixels)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b"")
    path.write_bytes(png)


def _paint(pixels, x, y, color, scale, glyph):
    height = len(pixels)
    width = len(pixels[0]) // 3
    for row_index, bits in enumerate(glyph):
        for col_index, bit in enumerate(bits):
            if bit != "1":
                continue
            for dy in range(scale):
                for dx in range(scale):
                    px = x + col_index * scale + dx
                    py = y + row_index * scale + dy
                    if 0 <= px < width and 0 <= py < height:
                        start = px * 3
                        pixels[py][start:start + 3] = color


def _text(pixels, x, y, text, color, scale):
    cursor = x
    for character in text.upper():
        glyph = FONT.get(character, FONT[" "])
        _paint(pixels, cursor, y, color, scale, glyph)
        cursor += 6 * scale


def _rgb_for(text):
    palette = {
        "red wall": (186, 58, 48),
        "blue wall": (47, 99, 176),
        "team a": (22, 128, 74),
        "team b": (198, 112, 28),
        "march": (37, 99, 168),
        "september": (146, 92, 28),
        "classmates": (88, 62, 158),
        "indoors": (48, 104, 122),
        "outdoors": (42, 122, 86),
    }
    return palette.get((text or "").lower(), (72, 86, 112))


def render(row):
    width, height = 640, 420
    accent = _rgb_for(row["visual_detail"] or row["people"] or row["month"] or row["indoors_outdoors"])
    base = (246, 244, 239)
    pixels = [bytearray(base * width) for _ in range(height)]
    for y in range(height):
        for x in range(18):
            start = x * 3
            pixels[y][start:start + 3] = bytearray(accent)
    ink = (28, 32, 38)
    _text(pixels, 48, 48, row["photo_id"], ink, 8)
    _text(pixels, 48, 150, (row["visual_detail"] or row["event"])[:18], accent, 6)
    _text(pixels, 48, 230, row["event"][:18], ink, 4)
    _text(pixels, 48, 290, "{m} {y}".format(m=row["month"], y=row["year"]), ink, 4)
    _text(pixels, 48, 350, (row["people"] or row["category"])[:18], (70, 78, 90), 3)
    path = ROOT / row["image_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    write_png(path, width, height, pixels)


def main():
    rows = catalog()
    write_csv(LIBRARY_PATH, LIBRARY_FIELDS, rows)
    task_fields = [
        "task_id", "target_photo_id", "memory_prompt", "difficulty",
        "expected_initial_cluster", "hidden_discriminator",
    ]
    task_rows = [
        dict(zip(task_fields, task))
        for task in TASKS
    ]
    write_csv(TASKS_PATH, task_fields, task_rows)
    if not RESULTS_PATH.exists() or RESULTS_PATH.stat().st_size == 0:
        write_csv(RESULTS_PATH, COLUMNS, [])
    for row in rows:
        render(row)
    print("photos", len(rows))


if __name__ == "__main__":
    main()
