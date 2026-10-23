"""Application entry point: wires the capture, recognizer and overlay together."""

import queue
import threading
from typing import Optional

from .audio import capture_loop
from .config import Config
from .overlay import CaptionOverlay
from .recognizer import recognize_loop


def run(config: Optional[Config] = None) -> None:
    config = config or Config()

    stop = threading.Event()
    audio_q: queue.Queue = queue.Queue(maxsize=config.max_queue_blocks)
    text_q: queue.Queue = queue.Queue()

    threading.Thread(
        target=capture_loop, args=(audio_q, text_q, stop, config), daemon=True
    ).start()
    threading.Thread(
        target=recognize_loop, args=(audio_q, text_q, stop, config), daemon=True
    ).start()

    CaptionOverlay(text_q, stop, config).run()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
