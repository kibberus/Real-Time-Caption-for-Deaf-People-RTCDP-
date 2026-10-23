"""Streaming speech recognition with Vosk."""

import json
import queue
import threading
import time
import traceback

import numpy as np
from vosk import KaldiRecognizer, Model, SetLogLevel

from .config import Config
from .messages import caption, status


def _load_model(config: Config) -> Model:
    if config.model_path:
        return Model(model_path=config.model_path)
    if config.model_name:
        return Model(model_name=config.model_name)
    return Model(lang=config.lang)


def _to_pcm16(chunk: np.ndarray) -> bytes:
    """Vosk wants 16-bit integer audio."""
    return (np.clip(chunk, -1.0, 1.0) * 32767).astype(np.int16).tobytes()


def recognize_loop(
    audio_q: queue.Queue,
    text_q: queue.Queue,
    stop: threading.Event,
    config: Config,
) -> None:
    """Feed audio to Vosk and send text updates to the overlay."""
    try:
        SetLogLevel(-1)  # hide Vosk's noisy logs
        text_q.put(status("Loading speech model..."))
        print("Loading Vosk model...")

        model = _load_model(config)
        recognizer = KaldiRecognizer(model, config.sample_rate)
        print("Model ready.")
        text_q.put(status("Ready. Play some audio."))

        last_sent = ""
        active = False   # True while there is sound being recognized
        quiet = 0.0      # seconds of silence since the last sound
        last_stats = time.monotonic()

        while not stop.is_set():
            if config.debug_stats and time.monotonic() - last_stats > 10:
                print("Audio queue size:", audio_q.qsize(), "| active:", active)
                last_stats = time.monotonic()

            try:
                chunk = audio_q.get(timeout=0.5)
            except queue.Empty:
                continue

            rms = float(np.sqrt(np.mean(chunk ** 2)))

            if rms >= config.silence_rms:
                active = True
                quiet = 0.0
            elif active:
                quiet += config.block_sec
                if quiet >= config.idle_after_sec:
                    # Long silence: flush the last words, then sleep
                    text = json.loads(recognizer.FinalResult()).get("text", "")
                    text_q.put(caption(text, True))
                    recognizer.Reset()
                    active = False
                    last_sent = ""
                    continue
            else:
                continue  # sleeping: skip silent audio completely

            if recognizer.AcceptWaveform(_to_pcm16(chunk)):
                # A full phrase just finished
                text = json.loads(recognizer.Result()).get("text", "")
                text_q.put(caption(text, True))
                last_sent = ""
            else:
                # Phrase still in progress: live partial text
                text = json.loads(recognizer.PartialResult()).get("partial", "")
                if text and text != last_sent:
                    text_q.put(caption(text, False))
                    last_sent = text
    except Exception as e:
        traceback.print_exc()
        text_q.put(status(f"RECOGNIZER ERROR: {e}"))
