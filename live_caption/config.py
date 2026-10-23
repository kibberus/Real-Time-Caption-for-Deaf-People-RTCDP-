"""All user-adjustable settings in one place."""

from dataclasses import dataclass
from typing import Optional

# This color becomes see-through (almost black, so text edges look clean)
TRANSPARENT_KEY = "#010101"


@dataclass(frozen=True)
class Config:
    # ---- Audio ----
    sample_rate: int = 16000          # Vosk models expect 16 kHz audio
    block_sec: float = 0.1            # small blocks = faster updates

    # ---- Speech model (the SMALL model is the lightest) ----
    lang: str = "en-us"
    model_name: Optional[str] = None  # None = default small model
    model_path: Optional[str] = None  # e.g. r"C:\models\vosk-model-small-en-us-0.15"

    # ---- Optimization ----
    max_queue_blocks: int = 30        # max audio waiting (30 x 0.1s = 3s)
    silence_rms: float = 0.002        # below this volume = silence
    idle_after_sec: float = 1.5       # silence before the recognizer sleeps
    debug_stats: bool = False         # print queue size every 10s

    # ---- Calm pacing ----
    refresh_sec: float = 0.35         # max screen update rate (higher = calmer)
    min_page_sec: float = 1.5         # minimum time a page stays visible
    clear_after_sec: float = 4.0      # captions vanish after this much quiet
    highlight_enabled: bool = True    # False = all words same color

    # ---- Look and feel ----
    bg_transparent: bool = True       # False = solid black bar
    font_family: str = "Segoe UI"
    font_size: int = 15
    window_width: int = 1000
    window_height: int = 90
    side_padding: int = 30
    fill_margin_px: int = 20          # safety space at the right edge
    text_color: str = "#FFFFFF"
    highlight_color: str = "#FFD400"
    msg_color: str = "#AAAAAA"
    show_drag_handle: bool = True
    handle_color: str = "#444444"
    poll_ms: int = 40                 # how often the window checks for new text
    msg_sec: float = 6.0              # how long status messages stay

    # ---- Derived values ----
    @property
    def bg(self) -> str:
        return TRANSPARENT_KEY if self.bg_transparent else "#000000"

    @property
    def max_text_width(self) -> int:
        return self.window_width - 2 * self.side_padding - self.fill_margin_px

    @property
    def block_frames(self) -> int:
        return int(self.sample_rate * self.block_sec)
