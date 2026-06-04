"""Coding scenes for Clawd — the crab peeking over a laptop, hard at work.

The classic "person behind a laptop" framing reads best at 16×16: eyestalks poke
up over the lid, the screen shows code, and the two pinchers tap the keyboard
(alternating left/right for a typing motion). Variants swap the screen content:
plain code, a terminal cursor, or a compiling asterisk.

Built from the same char-grid + palette system as clawd.py. Each scene is an
animation: a list of (Sprite, duration_ms). Exposed as playable "scenes".
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .clawd import CLAWD_PALETTE, Sprite, _canvas

# Laptop palette (uppercase keys, so they don't collide with Clawd's lowercase set).
CLAWD_PALETTE["G"] = (138, 142, 156)   # laptop body / keys
CLAWD_PALETTE["L"] = (198, 201, 212)   # bezel / lid edge
CLAWD_PALETTE["S"] = (18, 22, 40)      # dark screen
CLAWD_PALETTE["E"] = (108, 212, 138)   # green code text
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


# ---------- registry ----------

CODING_SPRITES: Dict[str, Sprite] = {
    "crab_type_a": Sprite("crab_type_a", CRAB_TYPE_A),
    "crab_type_b": Sprite("crab_type_b", CRAB_TYPE_B),
    "crab_tool_a": Sprite("crab_tool_a", CRAB_TOOL_A),
    "crab_tool_b": Sprite("crab_tool_b", CRAB_TOOL_B),
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
    # The earlier "peeking over the laptop" scenes, kept as playable options.
    "laptop": [(CODING_SPRITES["laptop_a"], 240), (CODING_SPRITES["laptop_b"], 240)],
    "terminal": [(CODING_SPRITES["term_a"], 520), (CODING_SPRITES["term_b"], 520)],
    "compile": [(CODING_SPRITES["compile_a"], 300), (CODING_SPRITES["compile_b"], 300)],
    "tooling": [(CODING_SPRITES["laptop_tool_a"], 280), (CODING_SPRITES["laptop_tool_b"], 280)],
}

# Which scene the looping `coding` state shows, and which the tool_use state uses.
DEFAULT_CODING_SCENE = "crabtype"
DEFAULT_TOOL_SCENE = "crabtool"
