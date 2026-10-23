# Live Caption

A calm, real-time caption overlay that listens to **any audio playing on your PC**
and shows it as captions on screen. Built as an accessibility tool for deaf and
hard-of-hearing users. Fully offline (Vosk).

## Features
- Transparent background (Windows): only the words are visible
- Left-aligned text that never shifts while you read it
- Line fills up first; a new page starts only when the next word does not fit
- Minimum page hold time and limited refresh rate (easy on the eyes)
- Current word highlighted by color (no animation)
- Lightweight: bounded audio queue and silence skipping

## Install
```bash
python -m pip install -r requirements.txt
```

## Run
```bash
python -m live_caption
# or, after `pip install -e .`
live-caption
```

## Controls
- **Left-click + drag** the small handle on the left: move the captions
- **Right-click** the handle or the text: quit

With a transparent background, clicks pass through empty areas, so use the handle to move the bar.

## Configuration
All settings live in `live_caption/config.py` (`Config` dataclass). Most useful:

| Setting | Purpose |
|---|---|
| `lang` / `model_path` | Which Vosk model to use |
| `refresh_sec` | Higher = calmer screen updates |
| `min_page_sec` | Minimum time a page stays visible |
| `highlight_enabled` | `False` = all words same color |
| `bg_transparent` | `False` = solid black bar |

To override without editing the file:
```python
from live_caption.app import run
from live_caption.config import Config
run(Config(font_size=18, lang="en-us"))
```

## Project layout
```
live-caption/
├── live_caption/
│   ├── __init__.py
│   ├── __main__.py      # python -m live_caption
│   ├── app.py           # wires threads + UI together
│   ├── config.py        # all settings
│   ├── messages.py      # queue message type
│   ├── audio.py         # system-audio capture (loopback)
│   ├── recognizer.py    # Vosk streaming recognition
│   ├── paging.py        # pure paging logic (unit tested)
│   └── overlay.py       # tkinter caption window
├── tests/
│   └── test_paging.py
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Architecture
```
capture thread --audio_q--> recognizer thread --text_q--> overlay (Tk main thread)
```

## Tests
```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```
