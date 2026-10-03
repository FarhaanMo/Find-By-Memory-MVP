"""Find by Memory. Streamlit interface for the existing search flow.

Run from the repository root:

    streamlit run mvp/app.py
"""

import html
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.flow import answer, elapsed_seconds, groups, new_state, none_of_these, select_photo, start_search, undo
from src.library import RESULTS_PATH, load_library, load_tasks
from src.log_session import COLUMNS, append_result, clean_participant, result_row

st.set_page_config(
    page_title="Find by Memory",
    page_icon=":camera:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(880px 380px at 50% 12%, rgba(219, 234, 254, 0.7), transparent 68%),
            #F7F8FC;
        color: #171717;
        color-scheme: light;
    }
    header[data-testid="stHeader"] { background: transparent; height: 0; }
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none; }
    .block-container { max-width: 1120px; padding-top: 1.1rem; padding-bottom: 3.5rem; }
    .brand { display: flex; align-items: center; gap: 0.55rem; font-weight: 650; letter-spacing: -0.02em; color: #1C1917; }
    .mark {
        width: 28px; height: 28px; border-radius: 8px; background: #1D4ED8;
        box-shadow: inset 0 0 0 7px #1D4ED8, inset 0 0 0 9px #DBEAFE;
    }
    .nav-current { color: #1C1917; font-weight: 650; border-bottom: 2px solid #1C1917; padding-bottom: 0.15rem; }
    .hero-mark {
        width: 46px; height: 46px; border-radius: 999px; border: 2px solid #BFDBFE;
        box-shadow: 0 0 0 8px rgba(219, 234, 254, 0.55); margin: 2.2rem auto 1rem;
    }
    .headline {
        font-family: Georgia, "Iowan Old Style", Palatino, "Palatino Linotype", serif;
        font-size: 2.7rem; line-height: 1.15; font-weight: 500; letter-spacing: -0.03em;
        text-align: center; color: #1C1917; margin: 0 0 0.7rem;
    }
    .support, .field-label, .section-copy, .question-copy { color: #57534E; }
    .support { text-align: center; font-size: 1.12rem; margin: 0 0 1.4rem; }
    .field-label { text-align: center; font-size: 0.95rem; margin: 0 0 0.45rem; }
    .try-label {
        text-align: center; letter-spacing: 0.14em; text-transform: uppercase;
        color: #78716C; font-size: 0.75rem; font-weight: 650; margin: 1.3rem 0 0.7rem;
    }
    .how-pill {
        margin: 1.6rem auto 0; max-width: 760px; background: #FFFFFF; border: 1px solid #E7E5E4;
        border-radius: 999px; padding: 0.55rem 0.9rem; color: #57534E; font-size: 0.92rem; text-align: center;
    }
    .memory-chip {
        display: inline-block; max-width: 100%; background: #FFFFFF; border: 1px solid #E7E5E4;
        border-radius: 999px; padding: 0.5rem 0.95rem; color: #44403C;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .kicker {
        color: #1D4ED8; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; margin: 0 0 0.35rem;
    }
    .question {
        font-size: 1.7rem; line-height: 1.25; font-weight: 620; letter-spacing: -0.03em;
        color: #1C1917; margin: 0 0 0.35rem;
    }
    .question-copy { margin: 0 0 0.8rem; }
    .count-pill {
        display: inline-block; background: #EFF6FF; color: #1D4ED8; border-radius: 999px;
        padding: 0.4rem 0.8rem; font-weight: 650; font-size: 0.95rem;
    }
    .section-title { font-size: 1.35rem; font-weight: 680; letter-spacing: -0.03em; margin: 0.2rem 0 0.15rem; }
    .section-copy { margin: 0 0 0.8rem; }
    .narrowed { color: #1C1917; font-weight: 650; margin: 0.2rem 0 0.6rem; }
    .found {
        font-family: Georgia, "Iowan Old Style", Palatino, serif;
        font-size: 2.6rem; text-align: center; letter-spacing: -0.03em; margin: 0.4rem 0 0.4rem;
    }
    .research-kicker { color: #78716C; font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 700; margin: 0; }
    div[data-testid="stForm"] {
        background: #FFFFFF; border: 1px solid #E7E5E4; border-radius: 999px;
        padding: 0.35rem 0.4rem 0.15rem 1rem;
        box-shadow: 0 10px 28px rgba(28, 25, 23, 0.05);
    }
    div[data-testid="stForm"] [data-testid="stHorizontalBlock"] { align-items: center; }
    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primaryFormSubmit"] {
        background: #2457E6 !important; background-color: #2457E6 !important;
        border: none !important; border-radius: 999px !important;
        color: #FFFFFF !important; font-weight: 650 !important;
    }
    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    button[data-testid="stBaseButton-primary"]:hover,
    button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
        background: #1D4ED8 !important; background-color: #1D4ED8 !important; color: #FFFFFF !important;
    }
    button[kind="primary"] p,
    button[kind="primaryFormSubmit"] p,
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primaryFormSubmit"] p { color: #FFFFFF !important; }
    button[kind="secondary"],
    button[kind="secondaryFormSubmit"],
    button[data-testid="stBaseButton-secondary"],
    button[data-testid="stBaseButton-secondaryFormSubmit"],
    div[data-testid="stDownloadButton"] button {
        background: #FFFFFF !important; background-color: #FFFFFF !important; color: #171717 !important;
        border: 1px solid #E7E5E4 !important; border-radius: 999px !important;
    }
    button[kind="secondary"]:hover,
    button[kind="secondaryFormSubmit"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover,
    button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    div[data-testid="stDownloadButton"] button:hover {
        background: #F8FAFC !important; background-color: #F8FAFC !important;
        color: #171717 !important; border-color: #D6D3D1 !important;
    }
    button[kind="secondary"] p,
    button[kind="secondaryFormSubmit"] p,
    button[data-testid="stBaseButton-secondary"] p,
    button[data-testid="stBaseButton-secondaryFormSubmit"] p,
    div[data-testid="stDownloadButton"] button p { color: #171717 !important; }
    button[kind="secondary"]:disabled,
    button[kind="secondaryFormSubmit"]:disabled,
    button[data-testid="stBaseButton-secondary"]:disabled,
    button[data-testid="stBaseButton-secondaryFormSubmit"]:disabled {
        background: #FFFFFF !important; background-color: #FFFFFF !important;
        color: #A8A29E !important; border-color: #E7E5E4 !important;
    }
    button[kind="secondary"]:disabled p,
    button[kind="secondaryFormSubmit"]:disabled p,
    button[data-testid="stBaseButton-secondary"]:disabled p,
    button[data-testid="stBaseButton-secondaryFormSubmit"]:disabled p { color: #A8A29E !important; }
    div[data-testid="stTextInput"] [data-baseweb="input"],
    div[data-testid="stTextInput"] [data-baseweb="base-input"],
    div[data-testid="stTextArea"] [data-baseweb="textarea"],
    div[data-testid="stTextArea"] [data-baseweb="base-input"] {
        background-color: #FFFFFF !important; color: #171717 !important;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important; color: #171717 !important;
        -webkit-text-fill-color: #171717 !important; caret-color: #171717 !important;
        border: 1px solid #E7E5E4 !important;
    }
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #78716C !important; -webkit-text-fill-color: #78716C !important; opacity: 1 !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
    div[data-baseweb="popover"] [data-baseweb="menu"],
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #FFFFFF !important; color: #171717 !important; border-color: #E7E5E4 !important;
    }
    div[data-baseweb="popover"] li,
    ul[data-testid="stSelectboxVirtualDropdown"] li,
    div[data-testid="stSelectbox"] [data-baseweb="select"] span,
    div[data-testid="stRadio"] label,
    div[data-testid="stWidgetLabel"] p { color: #171717 !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important; border-color: #E7E5E4 !important;
    }
    .element-container:has(.examples-anchor) + .element-container button,
    .element-container:has(.examples-anchor) + [data-testid="stLayoutWrapper"] button {
        border-radius: 999px !important; background-color: #FFFFFF !important; border: 1px solid #E7E5E4 !important;
        color: #171717 !important; font-weight: 550 !important; white-space: nowrap !important;
        min-height: 2.4rem !important;
    }
    .element-container:has(.quiet-anchor) + .element-container button,
    .element-container:has(.quiet-anchor) + [data-testid="stLayoutWrapper"] button {
        background-color: #FFFFFF !important; border: 1px solid #E7E5E4 !important; color: #171717 !important;
        box-shadow: none !important; font-weight: 550 !important;
    }
    [data-testid="stColumn"]:has(.photo-card) { position: relative; }
    [data-testid="stColumn"]:has(.is-selected) {
        outline: 3px solid #1D4ED8; outline-offset: 2px; border-radius: 18px;
    }
    [data-testid="stElementToolbar"] { display: none !important; }
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stMarkdown"]:has(.photo-card) {
        position: absolute; inset: 0; width: auto; height: auto; margin: 0; overflow: visible; z-index: 6; pointer-events: none;
    }
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stImage"],
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stImageContainer"],
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stFullScreenFrame"],
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stElementContainer"]:has(img),
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stFullScreenFrame"] > div {
        width: 100% !important;
    }
    [data-testid="stColumn"]:has(.photo-card) img {
        width: 100% !important; height: 210px !important; max-width: none !important;
        object-fit: cover !important; object-position: center !important; border-radius: 14px !important;
        pointer-events: none !important;
    }
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stElementContainer"]:has([data-testid="stButton"]) {
        position: static !important; height: 0 !important; min-height: 0 !important;
        margin: 0 !important; overflow: visible !important;
    }
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stButton"] {
        position: absolute !important; inset: 0 !important; z-index: 5 !important;
        width: auto !important; height: auto !important; margin: 0 !important;
    }
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stButton"] > div,
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stTooltipHoverTarget"],
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stTooltipIcon"] {
        position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important;
    }
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stButton"] button {
        width: 100% !important; height: 100% !important; min-height: 100% !important;
        background: transparent !important; border: none !important; color: transparent !important;
        box-shadow: none !important;
    }
    [data-testid="stColumn"]:has(.photo-card) [data-testid="stButton"] button p { color: transparent !important; }
    .tick {
        position: absolute; top: 12px; right: 12px; z-index: 6; width: 26px; height: 26px;
        border-radius: 999px; background: #1D4ED8; color: #FFFFFF; display: flex; align-items: center;
        justify-content: center; font-size: 14px; font-weight: 700;
    }
    .photo-empty { height: 210px; border-radius: 14px; background: #E7E5E4; }
    .element-container:has(.gallery-anchor),
    .element-container:has(.examples-anchor),
    .element-container:has(.quiet-anchor) { display: none; }
    .element-container:has(.success-photo) + .element-container,
    .element-container:has(.success-photo) + .element-container [data-testid="stImage"],
    .element-container:has(.success-photo) + .element-container [data-testid="stFullScreenFrame"],
    .element-container:has(.success-photo) + .element-container [data-testid="stFullScreenFrame"] > div {
        width: 100% !important;
    }
    .element-container:has(.success-photo) + .element-container img {
        width: 100% !important; height: 380px !important; object-fit: cover !important; object-position: center !important; border-radius: 18px !important;
    }
    @media (max-width: 1200px) {
        .headline { font-size: 2.2rem; }
        .element-container:has(.examples-anchor) + .element-container button { white-space: normal !important; }
        .element-container:has(.gallery-anchor) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        .element-container:has(.gallery-anchor) + [data-testid="stLayoutWrapper"] [data-testid="stColumn"] {
            flex: 1 1 46% !important; width: 46% !important; min-width: 46% !important; max-width: 50% !important;
        }
        .element-container:has(.examples-anchor) + .element-container [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        .element-container:has(.examples-anchor) + .element-container [data-testid="stColumn"] {
            flex: 1 1 30% !important; width: auto !important; min-width: 30%;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

EXAMPLES = [
    ("Birthday with friends", "birthday with school friends", "TASK01"),
    ("Football match", "football match with my team", "TASK03"),
    ("Sister's wedding", "my sister's wedding", "TASK02"),
    ("Sales-target screenshot", "screenshot of my sales targets", "TASK04"),
    ("Graduation photo", "my graduation photo", "TASK05"),
]

HOW = (
    "Find by Memory looks at the current possible photos and asks for one detail "
    "that would best separate them. Your answer helps narrow the results without "
    "requiring you to invent another search."
)


@st.cache_data
def library():
    return load_library()


@st.cache_data
def tasks():
    return load_tasks()


def mvp_state():
    if "mvp" not in st.session_state:
        st.session_state.mvp = new_state()
    state = st.session_state.mvp
    state.setdefault("highlight", None)
    state.setdefault("selected_photo_id", None)
    state.setdefault("confirmed_photo_id", None)
    state.setdefault("search_complete", False)
    state.setdefault("frozen_seconds", None)
    return state


def clear_selection(state):
    state["highlight"] = None
    state["selected_photo_id"] = None
    st.session_state["selected_photo_id"] = None


def select_candidate(state, photo_id):
    state["highlight"] = photo_id
    state["selected_photo_id"] = photo_id
    st.session_state["selected_photo_id"] = photo_id


def complete_search(state, photo_id):
    if state.get("search_complete"):
        return
    seconds = elapsed_seconds(state)
    state["frozen_seconds"] = seconds
    select_photo(state, photo_id)
    state["confirmed_photo_id"] = photo_id
    state["search_complete"] = True
    st.session_state["confirmed_photo_id"] = photo_id
    st.session_state["search_complete"] = True
    select_candidate(state, photo_id)
    if state.get("test_mode") and not state.get("logged"):
        task_target = ""
        for task in tasks():
            if task["task_id"] == state.get("task_id"):
                task_target = task["target_photo_id"]
                break
        append_result(
            RESULTS_PATH,
            result_row(
                state,
                task_target,
                datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                seconds,
            ),
        )
        state["logged"] = True


def research_on():
    value = st.query_params.get("research", "")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value) == "1"


def launch_mode(research):
    if not research:
        return "mvp"
    label = st.session_state.get("research_mode_label", "Find by Memory")
    return "baseline" if label == "Baseline" else "mvp"


def begin(memory, mode, task_id="", test_mode=False, participant="P01"):
    state = mvp_state()
    state["task_id"] = task_id
    state["participant_id"] = clean_participant(participant)
    state["test_mode"] = bool(test_mode)
    clear_selection(state)
    state["confirmed_photo_id"] = None
    state["search_complete"] = False
    state["frozen_seconds"] = None
    st.session_state["confirmed_photo_id"] = None
    st.session_state["search_complete"] = False
    with st.spinner("Looking through your memories..."):
        start_search(
            state,
            memory,
            library(),
            mode=mode,
            use_model=True,
            test_mode=bool(test_mode),
        )
    clear_selection(state)
    state["confirmed_photo_id"] = None
    state["search_complete"] = False
    state["frozen_seconds"] = None


def launch(memory, research, task_id=""):
    state = mvp_state()
    begin(
        memory,
        launch_mode(research),
        task_id=task_id if research else "",
        test_mode=research,
        participant=state.get("participant_id", "P01") if research else "P01",
    )


def fresh_search(state, research):
    participant = clean_participant(state.get("participant_id"))
    mode = state.get("mode", "mvp")
    fresh = new_state()
    if research:
        fresh["participant_id"] = participant
        fresh["mode"] = mode
        fresh["test_mode"] = True
    fresh["selected_photo_id"] = None
    fresh["confirmed_photo_id"] = None
    fresh["search_complete"] = False
    fresh["highlight"] = None
    st.session_state.mvp = fresh
    st.session_state["selected_photo_id"] = None
    st.session_state["confirmed_photo_id"] = None
    st.session_state["search_complete"] = False


def queue_action(action, **payload):
    payload["action"] = action
    st.session_state["mvp_action"] = payload


def apply_action():
    action = st.session_state.pop("mvp_action", None)
    if not action:
        return
    state = mvp_state()
    kind = action.get("action")
    if kind == "launch":
        launch(
            action.get("memory", ""),
            bool(action.get("research")),
            task_id=action.get("task_id") or "",
        )
    elif kind == "start_task":
        labels = st.session_state.get("research_task_labels") or []
        choice = st.session_state.get("research_task", "Select a task")
        rows = tasks()
        if choice == "Select a task" or choice not in labels:
            st.session_state["task_warning"] = True
            return
        task = rows[labels.index(choice) - 1]
        begin(
            task["memory_prompt"],
            launch_mode(True),
            task_id=task["task_id"],
            test_mode=True,
            participant=state.get("participant_id", "P01"),
        )
    elif kind == "answer":
        clear_selection(state)
        if action.get("use_model"):
            with st.spinner("Looking through your memories..."):
                answer(state, action.get("choice"), use_model=True)
        else:
            answer(state, action.get("choice"), use_model=False)
    elif kind == "undo":
        undo(state)
        clear_selection(state)
        state["frozen_seconds"] = None
    elif kind == "none":
        clear_selection(state)
        none_of_these(state)
    elif kind == "highlight":
        photo_id = action.get("photo_id")
        if photo_id:
            select_candidate(state, photo_id)
    elif kind == "cancel":
        clear_selection(state)
    elif kind == "confirm":
        photo_id = state.get("selected_photo_id") or state.get("highlight")
        if photo_id:
            complete_search(state, photo_id)
    elif kind == "fresh":
        fresh_search(state, bool(action.get("research")))
    elif kind == "edit":
        st.session_state["restore_memory"] = state.get("memory") or ""
        state["started"] = False
        clear_selection(state)
        state["chosen"] = None
        state["confirmed_photo_id"] = None
        state["search_complete"] = False
        st.session_state["confirmed_photo_id"] = None
        st.session_state["search_complete"] = False


def count_label(state):
    counts = state.get("counts") or []
    if not counts:
        return ""
    if len(counts) >= 2 and counts[-1] != counts[0]:
        return "{a} possible photos → {b}".format(a=counts[0], b=counts[-1])
    return "{n} possible photos".format(n=counts[-1])


def task_target_id(state):
    for task in tasks():
        if task["task_id"] == state.get("task_id"):
            return task["target_photo_id"]
    return ""


def chosen_rank(state):
    chosen = state.get("chosen") or ""
    for index, row in enumerate(state.get("candidates") or [], start=1):
        if row["photo_id"] == chosen:
            return index
    return 0


def find_photo(state, photo_id):
    for row in list(state.get("candidates") or []) + list(library()):
        if row["photo_id"] == photo_id:
            return row
    return None


def top_nav():
    brand, current = st.columns([1.4, 2])
    with brand:
        st.markdown(
            '<div class="brand"><span class="mark"></span>Find by Memory</div>',
            unsafe_allow_html=True,
        )
    with current:
        st.markdown('<span class="nav-current">Memories</span>', unsafe_allow_html=True)


def how_it_works():
    with st.expander("How this works"):
        st.write(HOW)


def gallery_rows(state):
    strong, rest = groups(state)
    last = state["answers"][-1] if state.get("answers") else ""
    if state.get("mode") == "mvp" and last in ("yes", "no") and rest:
        return strong, rest
    return list(state.get("candidates") or []), []


def draw_grid(rows, state):
    highlight = state.get("selected_photo_id") or state.get("highlight")
    for start in range(0, len(rows), 4):
        st.markdown('<div class="gallery-anchor"></div>', unsafe_allow_html=True)
        columns = st.columns(4)
        for column, row in zip(columns, rows[start:start + 4]):
            with column:
                photo_card(row, highlight)


def photo_card(row, highlight):
    photo_id = row["photo_id"]
    selected = highlight == photo_id
    with st.container(border=True):
        mark = '<span class="photo-card"></span>'
        if selected:
            mark += '<span class="is-selected"></span><span class="tick">✓</span>'
        st.markdown(mark, unsafe_allow_html=True)
        image = row.get("image_file")
        if image and Path(image).is_file():
            st.image(str(image), width="stretch")
        else:
            st.markdown('<div class="photo-empty"></div>', unsafe_allow_html=True)
        st.button(
            "Select",
            key="select_{id}".format(id=photo_id),
            help="Select this photo",
            on_click=queue_action,
            args=("highlight",),
            kwargs={"photo_id": photo_id},
        )


def selection_bar(state):
    selected = state.get("selected_photo_id") or state.get("highlight")
    if not selected or state.get("search_complete") or state.get("chosen"):
        return
    st.markdown("**1 photo selected**")
    _space, cancel, confirm = st.columns([3.2, 1.2, 1.5])
    with cancel:
        st.button(
            "Cancel selection",
            key="cancel_selection",
            width="stretch",
            on_click=queue_action,
            args=("cancel",),
        )
    with confirm:
        st.button(
            "This is the photo",
            key="confirm_photo",
            type="primary",
            width="stretch",
            on_click=queue_action,
            args=("confirm",),
        )


def question_card(state):
    pending = state.get("pending")
    if state.get("mode") != "mvp" or not pending or state.get("chosen") or state.get("search_complete"):
        return
    with st.container(border=True):
        copy, pill = st.columns([3.2, 1.2])
        with copy:
            st.markdown('<p class="kicker">One detail could help</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="question">{text}</p>'.format(text=html.escape(pending.get("text") or "")),
                unsafe_allow_html=True,
            )
            message = state.get("message") or ""
            if message.startswith("Narrowed") or message.startswith("One more"):
                st.markdown(
                    '<p class="question-copy">{text}</p>'.format(text=html.escape(message)),
                    unsafe_allow_html=True,
                )
            yes, no, unsure = st.columns(3)
            with yes:
                st.button(
                    "Yes",
                    type="primary",
                    width="stretch",
                    on_click=queue_action,
                    args=("answer",),
                    kwargs={"choice": "yes", "use_model": True},
                )
            with no:
                st.button(
                    "No",
                    width="stretch",
                    on_click=queue_action,
                    args=("answer",),
                    kwargs={"choice": "no", "use_model": True},
                )
            with unsure:
                st.button(
                    "Not sure",
                    width="stretch",
                    on_click=queue_action,
                    args=("answer",),
                    kwargs={"choice": "not_sure", "use_model": False},
                )
        with pill:
            label = count_label(state)
            if label:
                st.markdown(
                    '<div class="count-pill">{text}</div>'.format(text=html.escape(label)),
                    unsafe_allow_html=True,
                )


def secondary_actions(state, research):
    st.markdown('<div class="quiet-anchor"></div>', unsafe_allow_html=True)
    _space, undo_col, none_col = st.columns([3.4, 1.3, 1.2])
    with undo_col:
        st.button(
            "Undo last answer",
            disabled=not state.get("history"),
            width="stretch",
            on_click=queue_action,
            args=("undo",),
        )
    with none_col:
        st.button("None of these", width="stretch", on_click=queue_action, args=("none",))
    st.button(
        "Start another search",
        key="results_restart",
        on_click=queue_action,
        args=("fresh",),
        kwargs={"research": research},
    )


def screen_start(state, research):
    restored = st.session_state.pop("restore_memory", None)
    _left, mid, _right = st.columns([0.35, 3.3, 0.35])
    with mid:
        st.markdown('<div class="hero-mark"></div>', unsafe_allow_html=True)
        st.markdown(
            '<h1 class="headline">Find a photo from what you remember</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p class='support'>You don't need the exact date or perfect search words.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="field-label">What do you remember about the photo?</p>',
            unsafe_allow_html=True,
        )
        with st.form("memory_form", clear_on_submit=False):
            entry, action = st.columns([4.2, 1.5])
            field = {
                "label": "What do you remember about the photo?",
                "placeholder": "Birthday dinner with my school friends...",
                "label_visibility": "collapsed",
            }
            if restored is not None:
                field["value"] = restored
            with entry:
                memory = st.text_input(**field)
            with action:
                submitted = st.form_submit_button("Find my photo →", type="primary")
        if submitted:
            if not (memory or "").strip():
                st.caption("Describe anything you remember about the photo.")
            else:
                queue_action("launch", memory=memory, research=research, task_id="")
                st.rerun()
    st.markdown('<p class="try-label">Try an example</p>', unsafe_allow_html=True)
    st.markdown('<div class="examples-anchor"></div>', unsafe_allow_html=True)
    columns = st.columns(len(EXAMPLES))
    for column, (label, prompt, task_id) in zip(columns, EXAMPLES):
        with column:
            st.button(
                label,
                width="stretch",
                on_click=queue_action,
                args=("launch",),
                kwargs={
                    "memory": prompt,
                    "research": research,
                    "task_id": task_id if research else "",
                },
            )
    st.markdown(
        '<div class="how-pill"><strong>How this works:</strong> {text}</div>'.format(text=html.escape(HOW)),
        unsafe_allow_html=True,
    )


def screen_results(state, research):
    remembered, edit = st.columns([5.2, 0.8])
    with remembered:
        st.markdown(
            '<div class="memory-chip">Remembered: “{text}”</div>'.format(
                text=html.escape(state.get("memory") or "")
            ),
            unsafe_allow_html=True,
        )
    with edit:
        st.button("Edit", on_click=queue_action, args=("edit",))

    question_card(state)

    message = state.get("message") or ""
    if message.startswith("Narrowed") or message.startswith("Here are more"):
        st.markdown(
            '<p class="narrowed">{text}</p>'.format(text=html.escape(message)),
            unsafe_allow_html=True,
        )

    label = count_label(state)
    title, pill = st.columns([3.4, 1.3])
    with title:
        st.markdown('<p class="section-title">Possible matches</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-copy">These are the closest photos from what you remembered.</p>',
            unsafe_allow_html=True,
        )
    with pill:
        if label and not state.get("pending"):
            st.markdown(
                '<div class="count-pill">{text}</div>'.format(text=html.escape(label)),
                unsafe_allow_html=True,
            )

    selection_bar(state)
    primary, rest = gallery_rows(state)
    if primary:
        draw_grid(primary, state)
    if rest:
        st.markdown('<p class="section-copy">Still possible</p>', unsafe_allow_html=True)
        draw_grid(rest, state)
    if not primary and not rest:
        st.write(message or "No close matches in the demo library.")
    secondary_actions(state, research)
    how_it_works()


def screen_success(state, research):
    st.markdown('<h1 class="found">Found it ✓</h1>', unsafe_allow_html=True)
    st.markdown(
        "<p class='support'>Your remembered details helped narrow the possibilities.</p>",
        unsafe_allow_html=True,
    )
    photo = find_photo(state, state.get("confirmed_photo_id") or state.get("chosen"))
    _left, mid, _right = st.columns([1, 1.6, 1])
    with mid:
        if photo:
            st.markdown('<div class="success-photo"></div>', unsafe_allow_html=True)
            image = photo.get("image_file")
            if image and Path(image).is_file():
                st.image(str(image), width="stretch")
            else:
                st.markdown('<div class="photo-empty"></div>', unsafe_allow_html=True)
        _gap, action, _gap2 = st.columns([1, 2, 1])
        with action:
            st.button(
                "Start another search",
                key="success_restart",
                type="primary",
                width="stretch",
                on_click=queue_action,
                args=("fresh",),
                kwargs={"research": research},
            )


def research_controls(state):
    with st.container(border=True):
        st.markdown('<p class="research-kicker">Research</p>', unsafe_allow_html=True)
        st.caption("Participant ids only, such as P01. Separate from the public product.")
        if "research_participant" not in st.session_state:
            st.session_state.research_participant = state.get("participant_id") or "P01"
        participant = st.text_input("Participant ID", key="research_participant")
        state["participant_id"] = clean_participant(participant)
        task_rows = tasks()
        labels = ["Select a task"] + [
            "{i} · {m}".format(i=row["task_id"], m=row["memory_prompt"]) for row in task_rows
        ]
        st.session_state["research_task_labels"] = labels
        st.selectbox("Task", labels, key="research_task")
        st.radio("Mode", ["Baseline", "Find by Memory"], horizontal=True, key="research_mode_label")
        if st.session_state.pop("task_warning", False):
            st.caption("Choose a task to start.")
        if state.get("test_mode") and state.get("t0") and not state.get("search_complete"):
            elapsed = max(0, int(time.time() - state["t0"]))
            st.caption("Timer running · {n}s".format(n=elapsed))
        elif state.get("search_complete") and state.get("frozen_seconds") not in (None, ""):
            st.caption("Timer stopped · {n}s".format(n=state.get("frozen_seconds")))
        else:
            st.caption("Timer idle")
        st.button("Start task", type="primary", on_click=queue_action, args=("start_task",))


def research_footer(state):
    if state.get("search_complete") and state.get("test_mode"):
        target = task_target_id(state)
        rank = chosen_rank(state)
        confirmed = state.get("confirmed_photo_id") or state.get("chosen")
        found = "Yes" if target and confirmed == target else "No"
        counts = state.get("counts") or []
        seconds = state.get("frozen_seconds")
        time_text = "—" if seconds in (None, "") else "{n}s".format(n=seconds)
        mode_text = "Baseline" if state.get("mode") == "baseline" else "Find by Memory"
        with st.container(border=True):
            st.markdown('<p class="research-kicker">Research summary</p>', unsafe_allow_html=True)
            st.caption(
                "Participant {p} · Task {t} · {mode}".format(
                    p=html.escape(str(state.get("participant_id") or "")),
                    t=html.escape(str(state.get("task_id") or "—")),
                    mode=mode_text,
                )
            )
            st.caption(
                "Target found {found} · Time to target {time} · Interactions {n} · Clarification questions {q}".format(
                    found=found,
                    time=time_text,
                    n=state.get("interactions", 0),
                    q=len(state.get("questions") or []),
                )
            )
            st.caption(
                "Initial candidates {a} · Final candidates {b} · Manual scanning required {scan} · Undo used {undo} · None of these used {none}".format(
                    a=counts[0] if counts else "—",
                    b=counts[-1] if counts else "—",
                    scan="Yes" if rank and rank > 3 else "No",
                    undo="Yes" if state.get("undo_used") else "No",
                    none="Yes" if state.get("none_used") else "No",
                )
            )
    payload = RESULTS_PATH.read_bytes() if RESULTS_PATH.is_file() and RESULTS_PATH.stat().st_size else (",".join(COLUMNS) + "\n").encode("utf-8")
    st.download_button("Download test results", data=payload, file_name="test_results.csv", mime="text/csv")


def main():
    research = research_on()
    apply_action()
    state = mvp_state()
    top_nav()
    if research:
        research_controls(state)
    if not state["started"]:
        screen_start(state, research)
    elif state.get("search_complete") or state.get("chosen"):
        screen_success(state, research)
    else:
        screen_results(state, research)
    if research:
        research_footer(state)


main()
