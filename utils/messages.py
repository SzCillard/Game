import time
from typing import List, Tuple

_messages: List[Tuple[str, float]] = []


def add_message(text: str):
    _messages.append((text, time.time()))


def draw_messages(screen, font, screen_height: int, keep_secs: float = 3.0):
    y_offset = screen_height - 28
    now = time.time()
    # keep only recent
    keep = []
    for msg, ts in _messages:
        if now - ts < keep_secs:
            keep.append((msg, ts))
    _messages[:] = keep

    for msg, _ in reversed(_messages):
        surf = font.render(msg, True, (10, 10, 10))
        screen.blit(surf, (8, y_offset))
        y_offset -= 22
