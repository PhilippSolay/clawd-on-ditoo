"""Coding scenes for Clawd — the crab peeking over a laptop, hard at work.

The classic "person behind a laptop" framing reads best at 16×16: eyestalks poke
up over the lid, the screen shows code, and the two pinchers tap the keyboard
(alternating left/right for a typing motion). Variants swap the screen content:
plain code, a terminal cursor, or a compiling asterisk.

Built from the same char-grid + palette system as clawd.py. Each scene is an
animation: a list of (Sprite, duration_ms). Exposed as playable "scenes".
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

from .clawd import CLAWD_PALETTE, Sprite, _canvas
from .rotation import ShuffleBag

# Laptop palette (uppercase keys, so they don't collide with Clawd's lowercase set).
CLAWD_PALETTE["G"] = (138, 142, 156)   # laptop body / keys
CLAWD_PALETTE["L"] = (198, 201, 212)   # bezel / lid edge / whiteboard frame
CLAWD_PALETTE["S"] = (18, 22, 40)      # dark screen / marker ink / book text
CLAWD_PALETTE["E"] = (108, 212, 138)   # green code text / a checkmark
CLAWD_PALETTE["D"] = (240, 214, 92)    # rubber-duck yellow (brighter than 'a')
CLAWD_PALETTE["N"] = (232, 232, 224)   # whiteboard / open-book paper (bright)
# (reuses 'a' = Anthropic yellow, 'w' = white, 'o' = orange crab, 'k' = pupil)


# ---------- laptop: typing code (claws alternate-tap) ----------

LAPTOP_A = _canvas([
    "....k......k....",   # eyestalk pupils
    "....o......o....",
    "...oo......oo...",   # brow / shell hint behind the lid
    "..LLLLLLLLLLLL..",   # lid top
    "..LSSSSSSSSSSL..",   # screen top (dark)
    "..LSEEE.EE..SL..",   # code line
    "..LSEE.EEEE.SL..",   # code line
    "..LSE.EE.E..SL..",   # code line
    "..LSEEE.Ew..SL..",   # code line + cursor (w)
    "..LLLLLLLLLLLL..",   # hinge
    ".GGGGGGGGGGGGGG.",   # keyboard
    "ooGGGGGGGGGGGGo.",   # LEFT claw down (tapping), right claw up
    ".oGGGGGGGGGGGG..",   # left claw tip
    "................",
    "................",
    "................",
])

LAPTOP_B = _canvas([
    "....k......k....",
    "....o......o....",
    "...oo......oo...",
    "..LLLLLLLLLLLL..",
    "..LSSSSSSSSSSL..",
    "..LSEE.EEE..SL..",   # code shifted (a char "typed")
    "..LSEEE.EEE.SL..",
    "..LSE.EEE.E.SL..",
    "..LSEEEE.E..SL..",   # cursor off this frame (blink)
    "..LLLLLLLLLLLL..",
    ".GGGGGGGGGGGGGG.",
    ".oGGGGGGGGGGGGoo",   # RIGHT claw down, left claw up
    "..GGGGGGGGGGGGo.",   # right claw tip
    "................",
    "................",
    "................",
])


# ---------- terminal: blinking prompt cursor ----------

TERM_A = _canvas([
    "....k......k....",
    "....o......o....",
    "...oo......oo...",
    "..LLLLLLLLLLLL..",
    "..LSSSSSSSSSSL..",
    "..LSEE.EEE..SL..",   # a line of output
    "..LSE.EEEE..SL..",
    "..LSSSSSSSSSSL..",
    "..LSEw......SL..",   # prompt + cursor block ON
    "..LLLLLLLLLLLL..",
    ".GGGGGGGGGGGGGG.",
    "ooGGGGGGGGGGGGo.",
    ".oGGGGGGGGGGGG..",
    "................",
    "................",
    "................",
])

TERM_B = _canvas([
    "....k......k....",
    "....o......o....",
    "...oo......oo...",
    "..LLLLLLLLLLLL..",
    "..LSSSSSSSSSSL..",
    "..LSEE.EEE..SL..",
    "..LSE.EEEE..SL..",
    "..LSSSSSSSSSSL..",
    "..LSE.......SL..",   # cursor block OFF (blink)
    "..LLLLLLLLLLLL..",
    ".GGGGGGGGGGGGGG.",
    ".oGGGGGGGGGGGGoo",
    "..GGGGGGGGGGGGo.",
    "................",
    "................",
    "................",
])


# ---------- compiling: Anthropic asterisk pulses on screen ----------

COMPILE_A = _canvas([
    "....k......k....",
    "....o......o....",
    "...oo......oo...",
    "..LLLLLLLLLLLL..",
    "..LSSSSSSSSSSL..",
    "..LS...a....SL..",   # a small "+" forming
    "..LS..aaa...SL..",
    "..LS...a....SL..",
    "..LSSSSSSSSSSL..",
    "..LLLLLLLLLLLL..",
    ".GGGGGGGGGGGGGG.",
    "ooGGGGGGGGGGGGoo",
    ".oGGGGGGGGGGGGo.",
    "................",
    "................",
    "................",
])

COMPILE_B = _canvas([
    "....k......k....",
    "....o......o....",
    "...oo......oo...",
    "..LLLLLLLLLLLL..",
    "..LSSSSSSSSSSL..",
    "..LS..a.a.a.SL..",   # full Anthropic-ish asterisk burst
    "..LS...aaa..SL..",
    "..LS..a.a.a.SL..",
    "..LSSSSSSSSSSL..",
    "..LLLLLLLLLLLL..",
    ".GGGGGGGGGGGGGG.",
    "ooGGGGGGGGGGGGoo",
    ".oGGGGGGGGGGGGo.",
    "................",
    "................",
    "................",
])


# ---------- tool call: a gear pulses on the SAME laptop body ----------
# Shares rows 0-4 and 9-12 with the compile scene exactly, so switching between
# "thinking" (coding) and "tool call" only changes the screen icon — the crab and
# laptop never move, which kills the jarring full-screen flip.

LAPTOP_TOOL_A = _canvas([
    "....k......k....",
    "....o......o....",
    "...oo......oo...",
    "..LLLLLLLLLLLL..",
    "..LSSSSSSSSSSL..",
    "..LS..aaaa..SL..",   # gear / cog (hollow)
    "..LS..a..a..SL..",
    "..LS..aaaa..SL..",
    "..LSSSSSSSSSSL..",
    "..LLLLLLLLLLLL..",
    ".GGGGGGGGGGGGGG.",
    "ooGGGGGGGGGGGGoo",
    ".oGGGGGGGGGGGGo.",
    "................",
    "................",
    "................",
])

LAPTOP_TOOL_B = _canvas([
    "....k......k....",
    "....o......o....",
    "...oo......oo...",
    "..LLLLLLLLLLLL..",
    "..LSSSSSSSSSSL..",
    "..LS..aaaa..SL..",   # gear "ticks" (fills solid) — a working pulse
    "..LS..aaaa..SL..",
    "..LS..aaaa..SL..",
    "..LSSSSSSSSSSL..",
    "..LLLLLLLLLLLL..",
    ".GGGGGGGGGGGGGG.",
    "ooGGGGGGGGGGGGoo",
    ".oGGGGGGGGGGGGo.",
    "................",
    "................",
    "................",
])


# ---------- front-facing crab at the keyboard (the default coding look) ----------
# Big cute eyes facing forward, shell, and a laptop below he's typing on. The
# `crab_type_*` (green code) and `crab_tool_*` (yellow gear) frames share an
# IDENTICAL body — only the screen content changes — so coding<->tool swaps just
# the screen icon, never the whole crab.

_CRAB_TOP = [
    "...oo....oo.....",   # eyestalk tops
    "..owwo..owwo....",   # eye whites
    "..okwo..okwo....",   # pupils (forward) + highlight
    "..ooooooooooo...",   # shell top
    "oooooohoooooooo.",   # shell + cream highlight
    "oooooooooooooooo",   # shell
    "oodddoooodddoooo",   # shell shadow
    ".oo........oo...",   # arms emerge from the shell sides
    ".o.LLLLLLLLL.o..",   # laptop lid (arms at cols 1 / 13)
]
_CRAB_BOT = [
    ".ooGGGGGGGGGGo..",   # keyboard + claws on the keys
    "...GGGGGGGGGGG..",   # keyboard front edge
    "................",
    "................",
    "................",
]


def _crab(row9: str, row10: str):
    return _canvas(_CRAB_TOP + [row9, row10] + _CRAB_BOT)


CRAB_TYPE_A = _crab(".o.SEEE.EE.S.o..", ".o.SE.EE.EES.o..")   # typing — code
CRAB_TYPE_B = _crab(".o.SEE.EEE.S.o..", ".o.SEE.E.EES.o..")   # code shifted
CRAB_TOOL_A = _crab(".o.SaaaaaaaS.o..", ".o.Sa.aaa.aS.o..")   # tool — gear
CRAB_TOOL_B = _crab(".o.Saa.a.aaS.o..", ".o.SaaaaaaaS.o..")   # gear pulse


# ---------- three more ways to work (besides the keyboard) ----------
# All share the same front-facing head + shell (rows 0-6) as the crab-type scenes,
# so they read as the same crab — just a different way of getting the work done.

_HEAD = _CRAB_TOP[:7]   # eyes + shell, rows 0-6


def _working(*body_rows: str):
    """Build a front-facing working crab: the shared head/shell + 9 rows of props."""
    return _canvas(_HEAD + list(body_rows))


# 1. Rubber-duck debugging: he explains the bug to a little yellow duck. The duck
#    faces him (beak left); his right claw gestures as he "talks it through".
DUCK_TALK = _working(
    ".oo.......o.....",   # left claw at rest, right claw raised (gesturing)
    "..........o.....",
    "..........DDD...",   # duck: head
    "........ooDkD...",   # beak (o) points back at the crab + eye (k)
    "........ooDDDD..",   # bill + body
    "..........DDDD..",   # body
    "...........DD...",   # tail
    "................",
    "................",
)
DUCK_LISTEN = _working(
    ".oo......o......",   # claw lowered a beat (mid-gesture)
    "...............a",   # a little "!" of insight, top-right
    "..........DDD...",
    ".........DDkD...",   # duck blinks forward (eye shifted)
    "........ooDDDD..",
    "..........DDDD..",
    "...........DD...",
    "................",
    "................",
)


# 2. Whiteboard architecting: two boxes joined by an arrow on a framed board he
#    holds up; the marker claw taps a box, then a green check lands when it clicks.
WHITEBOARD_DRAW = _working(
    ".oo........oo...",   # arms hold the board
    "..LLLLLLLLLLLL..",   # board frame — top
    "..LNNNNNNNNNNL..",   # blank paper
    "..LNSSNSSNSSNL..",   # box — box — box (a little pipeline)
    "..LNSNNNNNNSNL..",   # arrow shaft between the outer boxes
    "..LNSSNSSNSSNL..",   # box bottoms
    "..LNNNNNNNNNNL..",
    "..LLLLLLLLLLLL..",   # board frame — bottom
    "................",
)
WHITEBOARD_CHECK = _working(
    ".oo........oo...",
    "..LLLLLLLLLLLL..",
    "..LNNNNNNNNNNL..",
    "..LNSSNSSNSSNL..",
    "..LNSNNEENNSNL..",   # a green check lands on the link — it all connects
    "..LNSSNSSNSSNL..",
    "..LNNNNNNNNNNL..",
    "..LLLLLLLLLLLL..",
    "................",
)


# 3. Reading the docs: an open book held up, eyes scanning the pages. A line of
#    text "advances" between frames to sell the reading.
READING_A = _working(
    ".oo........oo...",   # arms hold the book open
    ".oNNNNNNNNNNNNo.",   # page top
    ".oNSSSNNSSSSNNo.",   # text — left page / right page (spine at center)
    ".oNSSNNNSSSNNNo.",
    ".oNSSSNNSSNNNNo.",
    ".oNSNNNNSSSSNNo.",
    ".oNNNNNNNNNNNNo.",   # page bottom
    "..o..........o..",
    "................",
)
READING_B = _working(
    ".oo........oo...",
    ".oNNNNNNNNNNNNo.",
    ".oNSNNNNSSNNNNo.",   # text shifted — a line has been read
    ".oNSSSNNSSSSNNo.",
    ".oNSSNNNSSNNNNo.",
    ".oNSSSNNSSSNNNo.",
    ".oNNNNNNNNNNNNo.",
    "..o..........o..",
    "................",
)


# ---------- registry ----------

CODING_SPRITES: Dict[str, Sprite] = {
    "crab_type_a": Sprite("crab_type_a", CRAB_TYPE_A),
    "crab_type_b": Sprite("crab_type_b", CRAB_TYPE_B),
    "crab_tool_a": Sprite("crab_tool_a", CRAB_TOOL_A),
    "crab_tool_b": Sprite("crab_tool_b", CRAB_TOOL_B),
    "duck_talk": Sprite("duck_talk", DUCK_TALK),
    "duck_listen": Sprite("duck_listen", DUCK_LISTEN),
    "whiteboard_draw": Sprite("whiteboard_draw", WHITEBOARD_DRAW),
    "whiteboard_check": Sprite("whiteboard_check", WHITEBOARD_CHECK),
    "reading_a": Sprite("reading_a", READING_A),
    "reading_b": Sprite("reading_b", READING_B),
    "laptop_tool_a": Sprite("laptop_tool_a", LAPTOP_TOOL_A),
    "laptop_tool_b": Sprite("laptop_tool_b", LAPTOP_TOOL_B),
    "laptop_a": Sprite("laptop_a", LAPTOP_A),
    "laptop_b": Sprite("laptop_b", LAPTOP_B),
    "term_a": Sprite("term_a", TERM_A),
    "term_b": Sprite("term_b", TERM_B),
    "compile_a": Sprite("compile_a", COMPILE_A),
    "compile_b": Sprite("compile_b", COMPILE_B),
}

# Named coding animations: name -> list of (Sprite, duration_ms).
SCENES: Dict[str, List[Tuple[Sprite, int]]] = {
    # Front-facing crab at the keyboard (the default look).
    "crabtype": [(CODING_SPRITES["crab_type_a"], 240), (CODING_SPRITES["crab_type_b"], 240)],
    # Tool call: same crab body as `crabtype`, gear pulsing on screen.
    "crabtool": [(CODING_SPRITES["crab_tool_a"], 280), (CODING_SPRITES["crab_tool_b"], 280)],
    # Three more ways he works — for ambient variety while coding.
    "rubberduck": [(CODING_SPRITES["duck_talk"], 460), (CODING_SPRITES["duck_listen"], 520)],
    "whiteboard": [(CODING_SPRITES["whiteboard_draw"], 620), (CODING_SPRITES["whiteboard_check"], 620)],
    "reading": [(CODING_SPRITES["reading_a"], 560), (CODING_SPRITES["reading_b"], 560)],
    # The earlier "peeking over the laptop" scenes, kept as playable options.
    "laptop": [(CODING_SPRITES["laptop_a"], 240), (CODING_SPRITES["laptop_b"], 240)],
    "terminal": [(CODING_SPRITES["term_a"], 520), (CODING_SPRITES["term_b"], 520)],
    "compile": [(CODING_SPRITES["compile_a"], 300), (CODING_SPRITES["compile_b"], 300)],
    "tooling": [(CODING_SPRITES["laptop_tool_a"], 280), (CODING_SPRITES["laptop_tool_b"], 280)],
}

# Which scene the looping `coding` state shows, and which the tool_use state uses.
DEFAULT_CODING_SCENE = "crabtype"
DEFAULT_TOOL_SCENE = "crabtool"

# The special working looks mixed into the standard keyboard loop for variety.
WORK_SPECIALS = ["rubberduck", "whiteboard", "reading"]

# Roughly how long to hold one working look (~4-5s) before the next loop cycle.
_WORK_HOLD_MS = 4500

# About once a minute of working, Clawd breaks from the keyboard to do a special
# look. Time-based (not per-cycle odds) so it survives the constant coding<->tool
# flipping of a real session — otherwise the special never gets a turn.
_WORK_SPECIAL_EVERY_S = 60.0

# Draw the special looks from a shuffle-bag so they rotate through the full set in
# random order without clumping (a plain random pick repeats — see rotation.py).
_WORK_BAG = ShuffleBag(WORK_SPECIALS)

# Wall-clock of the last special shown (None until the first working cycle). A
# 1-element list so the module-level timer is a mutable holder, not a global-rebind.
_last_work_special: List[Optional[float]] = [None]


def _reset_work_special_clock(value: Optional[float] = None) -> None:
    """Reset the 'time since last special' clock (used by tests)."""
    _last_work_special[0] = value


def _work_special_due(now: float) -> bool:
    """True at most once per _WORK_SPECIAL_EVERY_S — and records that it fired."""
    last = _last_work_special[0]
    if last is None:                       # first working cycle: start the clock, no special yet
        _last_work_special[0] = now
        return False
    if now - last >= _WORK_SPECIAL_EVERY_S:
        _last_work_special[0] = now
        return True
    return False


def _hold(scene: List[Tuple[Sprite, int]], target_ms: int = _WORK_HOLD_MS) -> List[Tuple[Sprite, int]]:
    """Repeat a scene to about `target_ms` so a look reads as a held pose."""
    beat = sum(ms for _, ms in scene) or 1
    return scene * max(1, round(target_ms / beat))


def coding_loop(now: Optional[float] = None) -> List[Tuple[Sprite, int]]:
    """One working cycle. Mostly a stretch at the keyboard — but about once a minute
    it *leads* with a special look (rubber-duck debugging, whiteboard, docs) before
    settling back to the keyboard. Leading (not trailing) means the special still
    shows even when a tool call cuts the coding stretch short a second later. The
    CODING state calls this fresh each loop; `now` is injectable for tests."""
    now = time.time() if now is None else now
    if _work_special_due(now):
        # Special first (rotated, not clumped), then back to the keyboard.
        return _hold(SCENES[_WORK_BAG.draw()]) + _hold(SCENES[DEFAULT_CODING_SCENE])
    return _hold(SCENES[DEFAULT_CODING_SCENE])
