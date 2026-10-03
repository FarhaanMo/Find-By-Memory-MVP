# Find by Memory

Find a photo from a partial memory. This is a separate Streamlit app from the Discovery Agent.

## Problem

People rarely remember a photo by its exact date or a perfect search phrase. They remember a fragment: who was there, what the place looked like, or what the moment was.

## Hypothesis

Asking for one detail that separates the current possible photos will narrow the set more usefully than leaving the person to scan the first results alone.

## How Find by Memory works

You describe what you remember. The app shows the closest photos in a controlled demo library. It may ask up to two short questions. Each answer reorders those photos. You then choose the photo.

## Next Useful Question

The question is chosen from the photos still in play. It asks for the detail that best splits that group into different answers. You can answer Yes, No, or Not sure. Not sure does not push any group down. After two questions, the app stops asking and shows the closest photos.

When a language model is available, it only rewrites that question into ordinary words. When it is not, the app uses a fixed question. The screen does not say which one was used.

## Controlled demo library

The demo has 40 photos in everyday groups: a birthday, a football match, a wedding, a sales screenshot, a graduation, and a meal with friends. The same library is used for every run.

## Baseline vs Find by Memory

Both start from the same memory and the same first set of photos.

- Baseline: you scan that set and choose a photo. There is no clarification question.
- Find by Memory: the same first set, then the next useful question, then an updated set.

## Success measures

A completed research session records whether the target photo was chosen, how long it took, how many interactions were used, how the candidate count changed, and whether manual scanning, undo, or none of these was used.

## Research Mode

Add `?research=1` to the app address. The public screen stays the same, with a compact research panel added.

Use participant ids such as P01, P02, or P03. Choose a task, choose Baseline or Find by Memory, and start the task. The timer starts with the task and stops when the photo is confirmed. A short summary appears after that. Download test results saves the recorded rows as CSV. The same rows are appended to `mvp/data/test_results.csv` when the machine can store files.

## Local run

From the repository root:

```bash
streamlit run mvp/app.py
```

## Deployment

Deploy this app separately from the Discovery Agent.

- Main file: `mvp/app.py`
- Dependencies: `mvp/requirements.txt`
- Optional secret: `GROQ_API_KEY`

The app runs with no secret. On Streamlit Community Cloud, download the CSV after a session. The host may not keep local files.

## Limitations

This prototype uses a controlled 40-photo demo library. It does not connect to a user's real Google Photos account or reproduce Google's production retrieval system.

Retrieval is a weighted word match over that library, not a production search index. At most two clarification questions are asked. Placeholder images are simple labelled cards so the demo can run without personal photos.
