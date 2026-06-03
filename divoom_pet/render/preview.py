"""Offline preview rendering for composited frames — our stand-in for hardware.

Turns composited 256-RGB frames (Clawd + overlays) and takeover animations into
PNG stills / animated GIFs, upscaled for visibility. PIL is imported lazily here
only; the daemon never touches this module.

    python3 -m divoom_pet.render.preview previews/   # writes the live-content gallery
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

from .canvas import RGB, WIDTH
from .colors import COLORS
from .compositor import (
    CountBadge,
    Frame,
    ProgressBar,
    banner,
    compose,
    compose_animation,
)

Anim = List[Tuple[Frame, int]]


# -------------------- image helpers (PIL, lazy) --------------------


def _to_image(frame: Sequence[RGB], scale: int):
    from PIL import Image

    img = Image.new("RGB", (WIDTH, WIDTH))
    img.putdata([tuple(px) for px in frame])
    if scale != 1:
        img = img.resize((WIDTH * scale, WIDTH * scale), Image.NEAREST)
    return img


def save_png(frame: Sequence[RGB], path, scale: int = 14) -> None:
    _to_image(frame, scale).save(str(path))


def save_gif(frames: Anim, path, scale: int = 14) -> None:
    if not frames:
        return
    images = [_to_image(f, scale) for f, _ in frames]
    durations = [max(20, ms) for _, ms in frames]
    images[0].save(
        str(path),
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        disposal=2,
    )


# -------------------- the live-content gallery --------------------


def render_showcase(out_dir: str = "previews") -> List[Path]:
    """Build the Phase-1 proof gallery: progress bar, count badge, banner takeover,
    and a mini end-to-end session montage. Returns the written paths."""
    from divoom_pet.sprites import SPRITES, State, animation_for_state

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    green, amber, orange, black = (
        COLORS["green"], COLORS["yellow"], COLORS["orange"], COLORS["black"],
    )
    written: List[Path] = []

    def emit(name: str, frames: Anim) -> None:
        path = out / name
        save_gif(frames, path)
        written.append(path)

    # 1 — idle crab with a progress bar filling 0 → 100%.
    steps = 40
    fill: Anim = []
    for i in range(steps + 1):
        base = SPRITES["idle_open"] if (i // 3) % 2 == 0 else SPRITES["idle_breathe"]
        fill.append((compose(base, [ProgressBar(value=i / steps, fg=green)]), 100))
    fill.append((compose(SPRITES["idle_open"], [ProgressBar(value=1.0, fg=green)]), 700))
    emit("live_progress.gif", fill)

    # 2 — happy crab with a corner count badge stepping 0 → 3 (agents coming home).
    badge: Anim = []
    for n in range(4):
        for sprite in (SPRITES["happy_a"], SPRITES["happy_b"]):
            badge.append(
                (compose(sprite, [CountBadge(count=n, color=amber, backing=black)]), 300)
            )
    emit("live_badge.gif", badge)

    # 3 — a "MERGED" banner takeover.
    emit("live_banner_merged.gif", banner("MERGED", color=green))

    # 4 — thinking crab with a half-full orange bar (a task mid-flight).
    emit(
        "live_thinking.gif",
        compose_animation(animation_for_state(State.THINKING) * 4,
                          [ProgressBar(value=0.5, fg=orange)]),
    )

    # 5 — mini session montage: hatch → think(+filling bar) → tool → happy(+badge) → MERGED.
    montage: Anim = compose_animation([(SPRITES["hatch"], 1200)])
    for i in range(9):
        montage += compose_animation(
            animation_for_state(State.THINKING), [ProgressBar(value=i / 12, fg=orange)]
        )
    montage += compose_animation(
        animation_for_state(State.TOOL_USE), [ProgressBar(value=0.85, fg=orange)]
    )
    for sprite in (SPRITES["happy_a"], SPRITES["happy_b"], SPRITES["happy_a"]):
        montage.append(
            (compose(sprite, [CountBadge(count=3, color=amber, backing=black)]), 320)
        )
    montage += banner("MERGED", color=green)
    emit("live_session.gif", montage)

    # A couple of static stills for quick glances.
    save_png(compose(SPRITES["idle_open"], [ProgressBar(value=0.5, fg=green)]),
             out / "live_progress_50.png")
    save_png(compose(SPRITES["happy_a"], [CountBadge(count=3, color=amber, backing=black)]),
             out / "live_badge_3.png")
    written += [out / "live_progress_50.png", out / "live_badge_3.png"]

    return written


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "previews"
    paths = render_showcase(target)
    print(f"wrote {len(paths)} live-content previews to {target}/:")
    for p in paths:
        print(f"  {p}")
