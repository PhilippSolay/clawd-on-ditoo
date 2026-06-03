"""Procedurally generated animations — "live-created" content drawn from math + RNG,
no external art. Each generator returns a list of (frame, duration_ms) pairs, ready
for `PetController.play_takeover`. Built on Canvas, so they compose with everything.

Deterministic when you pass a `seed` (used by tests/previews); lively when you
don't (the daemon leaves it None so each celebration differs).
"""

from __future__ import annotations

import colorsys
import math
import random
from typing import List, Optional, Sequence, Tuple

from .canvas import BLACK, WIDTH, Canvas, RGB
from .colors import COLORS

Frame = List[RGB]
Anim = List[Tuple[Frame, int]]

# On-brand confetti palette (Anthropic-ish).
PARTY_COLORS: Sequence[RGB] = (
    COLORS["orange"], COLORS["green"], COLORS["magenta"],
    COLORS["yellow"], COLORS["cyan"], COLORS["red"],
)


def _hsv(h: float, s: float = 0.7, v: float = 1.0) -> RGB:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def confetti(frames: int = 28, count: int = 24, colors: Sequence[RGB] = PARTY_COLORS,
             bg: RGB = BLACK, ms: int = 70, seed: Optional[int] = None) -> Anim:
    """Colored bits raining down with a little sideways sway. A celebration."""
    rng = random.Random(seed)
    parts = [
        {
            "x": rng.uniform(0, WIDTH - 1),
            "y": rng.uniform(-WIDTH, 0),
            "c": rng.choice(colors),
            "v": rng.uniform(0.5, 1.4),
            "sway": rng.uniform(-0.7, 0.7),
            "ph": rng.uniform(0, 6.28),
        }
        for _ in range(count)
    ]
    out: Anim = []
    for f in range(frames):
        cv = Canvas(bg)
        for p in parts:
            y = p["y"] + p["v"] * f
            x = p["x"] + math.sin(f * 0.4 + p["ph"]) * p["sway"]
            cv.set_pixel(int(round(x)), int(round(y)), p["c"])
        out.append((cv.to_frame(), ms))
    return out


def fireworks(frames: int = 26, colors: Sequence[RGB] = PARTY_COLORS,
              center: Tuple[int, int] = (8, 8), ms: int = 70,
              seed: Optional[int] = None) -> Anim:
    """A ring bursting outward from center, fading as it expands."""
    rng = random.Random(seed)
    color = rng.choice(colors)
    cx, cy = center
    spokes = 12
    out: Anim = []
    for f in range(frames):
        cv = Canvas(BLACK)
        radius = f * 0.62
        fade = max(0.0, 1.0 - f / frames)
        col = tuple(int(ch * fade) for ch in color)
        for i in range(spokes):
            angle = 2 * math.pi * i / spokes
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            cv.set_pixel(int(round(x)), int(round(y)), col)
        out.append((cv.to_frame(), ms))
    return out


def plasma(frames: int = 32, ms: int = 80, sat: float = 0.7) -> Anim:
    """A smooth, color-cycling sine field. Ambient eye-candy."""
    out: Anim = []
    for f in range(frames):
        cv = Canvas()
        t = f * 0.3
        for y in range(WIDTH):
            for x in range(WIDTH):
                v = (math.sin(x * 0.6 + t)
                     + math.sin(y * 0.5 - t)
                     + math.sin((x + y) * 0.4 + t)) / 3.0  # -1..1
                cv.set_pixel(x, y, _hsv((v + 1) / 2, sat, 1.0))
        out.append((cv.to_frame(), ms))
    return out


def pulse(color: RGB = COLORS["magenta"], frames: int = 20, ms: int = 60) -> Anim:
    """A full-screen brightness heartbeat in one color."""
    out: Anim = []
    for f in range(frames):
        k = (math.sin(f / frames * 2 * math.pi) + 1) / 2  # 0..1
        cv = Canvas(tuple(int(ch * k) for ch in color))
        out.append((cv.to_frame(), ms))
    return out


def sparkle_over(base, frames: int = 18, count: int = 6,
                 color: RGB = COLORS["cream"], ms: int = 90,
                 seed: Optional[int] = None) -> Anim:
    """Twinkling sparkles over a base sprite/frame (e.g. a happy Clawd)."""
    from .compositor import compose

    rng = random.Random(seed)
    base_frame = compose(base)
    out: Anim = []
    for _ in range(frames):
        cv = Canvas()
        cv.blit_frame(base_frame)
        for _ in range(count):
            if rng.random() < 0.6:
                cv.set_pixel(rng.randint(0, WIDTH - 1), rng.randint(0, WIDTH - 1), color)
        out.append((cv.to_frame(), ms))
    return out


def celebrate(base, frames: int = 26, ms: int = 70, seed: Optional[int] = None) -> Anim:
    """Confetti raining over a base sprite (Clawd stays visible underneath)."""
    from .compositor import compose

    rng = random.Random(seed)
    base_frame = compose(base)
    parts = [
        {"x": rng.uniform(0, WIDTH - 1), "y": rng.uniform(-WIDTH, 0),
         "c": rng.choice(PARTY_COLORS), "v": rng.uniform(0.6, 1.5),
         "sway": rng.uniform(-0.6, 0.6), "ph": rng.uniform(0, 6.28)}
        for _ in range(18)
    ]
    out: Anim = []
    for f in range(frames):
        cv = Canvas()
        cv.blit_frame(base_frame)
        for p in parts:
            y = p["y"] + p["v"] * f
            x = p["x"] + math.sin(f * 0.4 + p["ph"]) * p["sway"]
            cv.set_pixel(int(round(x)), int(round(y)), p["c"])
        out.append((cv.to_frame(), ms))
    return out


# Name → zero-arg-callable map for the live `effect` event.
EFFECTS = {
    "confetti": confetti,
    "fireworks": fireworks,
    "plasma": plasma,
    "pulse": pulse,
}
