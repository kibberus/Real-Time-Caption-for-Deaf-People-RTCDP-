"""Transparent always-on-top caption window (tkinter, Windows)."""

import queue
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import List

from .config import TRANSPARENT_KEY, Config
from .messages import KIND_MSG, Message
from .paging import Paginator


class CaptionOverlay:
    def __init__(self, text_q: queue.Queue, stop: threading.Event, config: Config):
        self.cfg = config
        self.text_q = text_q
        self.stop = stop

        self.base: List[str] = []     # words of finished phrases on this page
        self.current: List[str] = []  # words of the phrase still being spoken
        self.shown: List[str] = []    # words actually on screen right now
        self.message = ""             # status message ("Ready...", errors)
        self.msg_time = 0.0
        self.last_update = 0.0        # last time new text arrived
        self.last_refresh = 0.0       # last time the screen text changed
        self.page_started = 0.0       # when the current page first appeared
        self.last_signature = None

        self._build_window()
        self._build_widgets()
        self._bind_events()

        self.paginator = Paginator(self.font.measure, config.max_text_width)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(config.poll_ms, self._tick)

    # ---- construction ----
    def _build_window(self) -> None:
        cfg = self.cfg
        self.root = tk.Tk()
        self.root.title("Live Caption")
        self.root.overrideredirect(True)          # no title bar
        self.root.attributes("-topmost", True)    # always on top
        self.root.configure(bg=cfg.bg)

        if cfg.bg_transparent:
            # Everything painted in the key color becomes see-through (Windows)
            self.root.attributes("-transparentcolor", TRANSPARENT_KEY)
            self.root.attributes("-alpha", 1.0)
        else:
            self.root.attributes("-alpha", 0.9)

        x = (self.root.winfo_screenwidth() - cfg.window_width) // 2
        y = self.root.winfo_screenheight() - cfg.window_height - 80
        self.root.geometry(f"{cfg.window_width}x{cfg.window_height}+{x}+{y}")

    def _build_widgets(self) -> None:
        cfg = self.cfg
        self.font = tkfont.Font(
            family=cfg.font_family, size=cfg.font_size, weight="bold"
        )

        self.text = tk.Text(
            self.root,
            font=self.font,
            bg=cfg.bg,
            fg=cfg.text_color,
            bd=0,
            highlightthickness=0,
            wrap="none",
            height=1,
            cursor="arrow",
            state="disabled",
        )
        self.text.tag_configure("center", justify="center")
        self.text.tag_configure("current", foreground=cfg.highlight_color)
        self.text.tag_configure("msg", foreground=cfg.msg_color)
        # Left-aligned and fixed in place, so the words you read never move
        self.text.pack(expand=True, fill="x", padx=cfg.side_padding)

        # Small solid handle: the part you can grab when the background is see-through
        self.handle = None
        if cfg.show_drag_handle:
            self.handle = tk.Frame(
                self.root, bg=cfg.handle_color, width=8, height=36, cursor="fleur"
            )
            self.handle.place(x=8, rely=0.5, anchor="w")

    def _bind_events(self) -> None:
        self._drag_x = 0
        self._drag_y = 0
        widgets = [self.root, self.text] + ([self.handle] if self.handle else [])
        for widget in widgets:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)
            widget.bind("<Button-3>", lambda e: self.close())

    # ---- window dragging ----
    def _start_drag(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()
        return "break"

    def _do_drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")
        return "break"

    # ---- incoming text ----
    def _on_text(self, text: str, finished: bool) -> None:
        self.message = ""
        words = text.split()
        if words:
            self.current = words

        if finished:
            if self.current:
                self.base = self.paginator.newest_page(self.base + self.current)
            self.current = []

    # ---- drawing (only when something actually changed) ----
    def _render(self, words: List[str], message: str) -> None:
        signature = (tuple(words), message)
        if signature == self.last_signature:
            return
        self.last_signature = signature

        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        if message:
            self.text.insert("end", message, ("center", "msg"))
        else:
            for i, word in enumerate(words):
                is_last = i == len(words) - 1
                if self.cfg.highlight_enabled and is_last:
                    self.text.insert("end", word, "current")
                else:
                    self.text.insert("end", word)
                if not is_last:
                    self.text.insert("end", " ")
        self.text.config(state="disabled")

    def _maybe_show(self, target: List[str], now: float) -> None:
        """Update the screen, but calmly: limited rate and page hold time."""
        if target == self.shown:
            return
        if self.shown and target and target[0] != self.shown[0]:
            # This would start a NEW page: wait until the old one was readable
            if now - self.page_started < self.cfg.min_page_sec:
                return
            self.page_started = now
        elif not self.shown:
            self.page_started = now
        self.shown = target
        self.last_refresh = now

    def _clear_all(self) -> None:
        self.base = []
        self.current = []
        self.shown = []

    # ---- main loop ----
    def _drain_queue(self, now: float) -> None:
        try:
            while True:
                msg: Message = self.text_q.get_nowait()
                if msg.kind == KIND_MSG:
                    self._clear_all()
                    self.message = msg.text
                    self.msg_time = now
                else:
                    self._on_text(msg.text, bool(msg.finished))
                    self.last_update = now
        except queue.Empty:
            pass

    def _tick(self) -> None:
        cfg = self.cfg
        now = time.monotonic()

        self._drain_queue(now)

        # Clear captions after a quiet period
        if (self.base or self.current) and now - self.last_update > cfg.clear_after_sec:
            self._clear_all()

        # Hide status messages after a while
        if self.message and now - self.msg_time > cfg.msg_sec:
            self.message = ""

        if self.message:
            self._render([], self.message)
        else:
            if (self.base or self.current) and now - self.last_refresh >= cfg.refresh_sec:
                self._maybe_show(
                    self.paginator.newest_page(self.base + self.current), now
                )
            self._render(self.shown, "")

        self.root.after(cfg.poll_ms, self._tick)

    def close(self) -> None:
        self.stop.set()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
