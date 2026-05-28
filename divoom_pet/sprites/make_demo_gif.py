"""Render a single animated GIF that cycles through every Clawd state.

Run:
    python3 -m divoom_pet.sprites.make_demo_gif previews/clawd-demo.gif
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple

from PIL import Image

from divoom_pet.sprites import (
    CLAWD_PALETTE,
    State,
    animation_for_state,
)

SCALE = 16  # upscale 16x16 -> 256x256 for visibility


def _sprite_to_image(sprite) -> Image.Image:
    img = Image.new("RGB", (16, 16), (0, 0, 0))
    px = img.load()
    for y, row in enumerate(sprite.rows):
        for x, ch in enumerate(row):
            px[x, y] = CLAWD_PALETTE.get(ch, (0, 0, 0))
    return img.resize((16 * SCALE, 16 * SCALE), Image.NEAREST)


def make_demo(out_path: str) -> None:
    sequence: List[Tuple[State, int]] = [
        (State.HATCH, 1),
        (State.THINKING, 3),
        (State.TYPING, 4),
        (State.TOOL_USE, 3),
        (State.HAPPY, 2),
        (State.ALERT, 2),
        (State.SLEEPING, 2),
        (State.IDLE, 1),
    ]
    frames: List[Image.Image] = []
    durations: List[int] = []  # ms
    for state, reps in sequence:
        anim = animation_for_state(state)
        for _ in range(reps):
            for sprite, duration_ms in anim:
                frames.append(_sprite_to_image(sprite))
                durations.append(max(60, duration_ms))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    total = sum(durations) / 1000.0
    print(f"wrote {out_path}: {len(frames)} frames, {total:.1f}s loop")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "previews/clawd-demo.gif"
    make_demo(out)
