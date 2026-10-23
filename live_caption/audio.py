"""System-audio capture (loopback of the default speakers)."""

import queue
import threading
import traceback

import numpy as np
import soundcard as sc

from .config import Config
from .messages import status


def put_latest(q: queue.Queue, item) -> None:
    """Put an item in a bounded queue; if it is full, drop the oldest item."""
    try:
        q.put_nowait(item)
    except queue.Full:
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        try:
            q.put_nowait(item)
        except queue.Full:
            pass


def capture_loop(
    audio_q: queue.Queue,
    text_q: queue.Queue,
    stop: threading.Event,
    config: Config,
) -> None:
    """Record system audio and push mono float32 blocks into audio_q."""
    try:
        speaker = sc.default_speaker()
        print("Using default speaker:", speaker.name)

        mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)

        with mic.recorder(samplerate=config.sample_rate, channels=1) as rec:
            print("Audio capture started.")
            while not stop.is_set():
                data = rec.record(numframes=config.block_frames)
                put_latest(audio_q, data[:, 0].astype(np.float32))
    except Exception as e:
        traceback.print_exc()
        text_q.put(status(f"CAPTURE ERROR: {e}"))
