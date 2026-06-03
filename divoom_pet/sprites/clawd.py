"""Pixel-art sprites for Clawd the orange Anthropic crab.

Each sprite is a 16-row × 16-column string. Each character maps to a palette entry.
Color choices:
  '.' transparent / black background
  'o' Clawd orange       — Anthropic primary  #d97757
  'd' deeper rust        — shell shadow       #a44e36
  'h' highlight cream    — shell shine        #f4d4b5
  'k' eye/pupil black                          #050505
  'w' eye white                                #fefdf9
  'r' alert red                                #d6433a
  'm' heart magenta                            #e35a8b
  'a' Anthropic asterisk yellow                #f2c463
  'p' sleepy purple/blue z                     #6a9bcc
  'c' cream highlight                          #faf9f5
"""

from __future__ import annotations

import enum
import random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

RGB = Tuple[int, int, int]

CLAWD_PALETTE: Dict[str, RGB] = {
    ".": (0, 0, 0),
    "o": (217, 119, 87),
    "d": (164, 78, 54),
    "h": (244, 212, 181),
    "k": (5, 5, 5),
    "w": (254, 253, 249),
    "r": (214, 67, 58),
    "m": (227, 90, 139),
    "a": (242, 196, 99),
    "p": (106, 155, 204),
    "c": (250, 249, 245),
}


# -------------------- canvas helpers --------------------


def _row(s: str) -> str:
    """Validate and pad/trim a sprite row to exactly 16 chars."""
    if len(s) > 16:
        raise ValueError(f"row too wide: {s!r}")
    return s.ljust(16, ".")


def _canvas(rows: Sequence[str]) -> List[str]:
    if len(rows) > 16:
        raise ValueError(f"too many rows: {len(rows)}")
    out = [_row(r) for r in rows]
    while len(out) < 16:
        out.append(".".rjust(16, "."))
    return out


# -------------------- Clawd sprites --------------------
# Crab silhouette: eyestalks on rows 2-4, body shell rows 5-9, legs/claws rows 10-12.

CLAWD_PALETTE["-"] = (60, 30, 20)  # half-lid color used for blink

# ---------- Clawd redesigned: wide shell, visible pincher claws, 6 legs ----------
#
# Body anatomy (in rows):
#   row 1-2: eye pupils on tall stalks
#   row 3-4: eyestalks descending into shell
#   row 5:   top arc of shell + tops of pinchers at far edges
#   row 6-8: full shell body, ear-to-ear; pinchers protrude at cols 0-1 and 14-15
#   row 9:   shell underbelly with darker shading
#   row 10:  leg attachments (6 legs total)
#   row 11:  leg knees splaying out
#   row 12:  leg tips
#
# Idle uses 'h' for cream highlights on the shell, 'd' for shadow underside.

IDLE_OPEN = _canvas([
    "................",
    "....k......k....",
    "....o......o....",  # eyestalks
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",  # top of shell (curves down at sides for pincher tops)
    "ooooohoooohoooo.",  # full shell + cream highlights + pincher attachments
    "oooooooooooooooo",  # shell wraps wall-to-wall (incl. pinchers)
    "oodddoooodddoooo",  # shell with shadow
    ".ooooooooooooooo",  # bottom curve, slight asymmetry
    "..o.o.oo.oo.o.o.",  # 6 legs poking out
    "..o.o.oo.oo.o.o.",  # leg knees
    "..o...o..o...o..",  # leg tips
    "................",
    "................",
    "................",
])

IDLE_BLINK = _canvas([
    "................",
    "....-......-....",  # half-closed lids
    "....o......o....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])


# Thinking: asterisk above + claws/pinchers slightly raised
THINKING_A = _canvas([
    ".......a........",
    "....a..a..a.....",
    ".....aaaaa......",
    "....k.aaa..k....",
    "....o..a...o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

THINKING_B = _canvas([
    "....a...........",
    "....a..a........",
    "...a.aaa.a......",
    "....aakaa..k....",
    "....o..a...o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

THINKING_C = _canvas([
    "............a...",
    "........a...a...",
    "........aaaaa...",
    "....k....aka....",
    "....o...a..a.o..",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])


# Typing: claws/pinchers extend higher, mouth opens-and-closes
TYPING_UP = _canvas([
    "................",
    "....k......k....",
    "....o......o....",
    "....o......o....",
    "oo..o......o..oo",  # pinchers REACHED UP
    "ooooooooooooooo.",  # shell still solid
    "ooohohoooohohooo",
    "oooo..oooo..oooo",  # mouth slightly open
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
    "................",
])

TYPING_DOWN = _canvas([
    "................",
    "....k......k....",
    "....o......o....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "ooooooooooooooo.",
    "oodddoooodddoooo",
    "oooooo...oooooo.",   # mouth wider open ("oh")
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
    "................",
])


# Tool use: gear icon top-right, one claw raised pointing at it
TOOL_USE = _canvas([
    "..........aaa...",
    ".........a.a.a..",  # gear teeth
    "..........aka...",  # gear with center pupil
    ".........a.a.a..",
    "....k.....aaa...",
    "....o...........",
    "....o....o......",
    "....o....o......",  # one claw raised
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
])


# Happy: heart pop above + smiley shell
HAPPY_A = _canvas([
    "................",
    "....mm...mm.....",
    "...mmmm.mmmm....",
    "...mmmmmmmmm....",
    "....mmmmmmm.....",
    ".....mmmmm......",
    "......mmm.......",
    ".......m........",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "ooookoooookoooo.",   # smile eyes (squinted joy)
    "ooooohhhhhooooo.",   # big smile
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "................",
])

HAPPY_B = _canvas([
    "................",
    "................",
    "....k......k....",
    "....o......o....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "oooooohhhhooooo.",   # smile mid-shell
    "ooooooooooooooo.",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])


# Alert: red ring flash, wide white eyes, claws THRUST upward
ALERT_A = _canvas([
    "rr...........rr.",
    "rr...w....w..rr.",
    "r....w....w...r.",   # shocked white eyes
    "r....o....o...r.",
    "rrr..o....o.rrr.",
    "rooooooooooooor.",   # red outline around shell
    "rooohoooohooor..",
    "rooooooooooooor.",
    "roodddoooodddor.",
    "rooooooooooooor.",
    "r.o.o.oo.oo.o.r.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
    "................",
])

ALERT_B = _canvas([
    "................",
    ".....w....w.....",
    ".....w....w.....",
    "....ko....ok....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
    "................",
])


# Sleeping: body curled, "z" rising over time
SLEEP_A = _canvas([
    "................",
    "................",
    "................",
    "..........p.....",
    "..........p.....",   # tiny z (1 segment)
    "................",
    "................",
    "...oooooooooo...",
    "..oooohoohoooo..",   # eyes closed (no pupils)
    "..oooooooooooo..",   # body sideways
    "..oodddooooddoo.",
    "...o.o.o.o.o.o..",
    "................",
    "................",
    "................",
    "................",
])

SLEEP_B = _canvas([
    "................",
    "................",
    ".........ppp....",
    ".........p......",
    "........pp......",
    ".........ppp....",
    "................",
    "...oooooooooo...",
    "..oooohoohoooo..",
    "..oooooooooooo..",
    "..oodddooooddoo.",
    "...o.o.o.o.o.o..",
    "................",
    "................",
    "................",
    "................",
])

SLEEP_C = _canvas([
    "................",
    "....pppp........",
    "....p..p........",
    "...p..p.........",
    "..p..p..........",
    "..pppp..........",
    "................",
    "...oooooooooo...",
    "..oooohoohoooo..",
    "..oooooooooooo..",
    "..oodddooooddoo.",
    "...o.o.o.o.o.o..",
    "................",
    "................",
    "................",
    "................",
])


# Hatch: big Anthropic asterisk that resolves into Clawd
HATCH = _canvas([
    ".......a........",
    "....a..a..a.....",
    ".....a.a.a......",
    "....aaaaaaa.....",
    ".....a.a.a......",
    "....a..a..a.....",
    ".......a........",
    "................",
    "....k......k....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
])


# ---------- idle "aliveness" frames ----------
# A constant breathing bob plus a set of rare micro-fidgets (look around, wave,
# blow a bubble, stretch). animation_for_state(IDLE) composes these at random so
# Clawd never loops identically. Technique cribbed from Shimeji/desktop-pet idle
# tables: breathing constant, blinks decoupled + jittered, fidgets weighted-rare.

# Exhale: whole crab shifted down 1px. Alternating with IDLE_OPEN = breathing.
IDLE_BREATHE = _canvas([
    "................",
    "................",
    "....k......k....",
    "....o......o....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
])

# Glance left: pupils slide 1px left of their stalks.
IDLE_LOOK_L = _canvas([
    "................",
    "...k......k.....",
    "....o......o....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

# Glance right: pupils slide 1px right of their stalks.
IDLE_LOOK_R = _canvas([
    "................",
    ".....k......k...",
    "....o......o....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

# Wave hello: left pincher raised, open prongs. Two tilts = a side-to-side wave.
WAVE_UP = _canvas([
    "o.o.............",
    ".o..k......k....",
    ".o..o......o....",
    "..o.o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

WAVE_UP2 = _canvas([
    ".o.o............",
    "..o.k......k....",
    "..o.o......o....",
    "...oo......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

# Blow a bubble (crab is underwater, after all). Forms at the mouth, rises, pops.
BUBBLE_1 = _canvas([
    "................",
    "....k......k....",
    "....o......o....",
    "....o......o....",
    "....o..cc..o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

BUBBLE_2 = _canvas([
    ".......cc.......",
    "......c..c......",
    "......c..c..k...",
    "....k.c..c......",
    "....o..cc..o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

BUBBLE_POP = _canvas([
    "......w.w.w.....",
    ".....w..k..w....",
    ".......w.w......",
    "....k......k....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
])

# Big stretch: both pinchers thrown up high. The rare, satisfying idle fidget.
STRETCH = _canvas([
    "oo..k......k..oo",
    "oo..o......o..oo",
    ".o..o......o..o.",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
    "................",
])


# -------------------- types --------------------


@dataclass(frozen=True)
class Sprite:
    name: str
    rows: List[str]


class State(str, enum.Enum):
    IDLE = "idle"
    THINKING = "thinking"
    TYPING = "typing"
    TOOL_USE = "tool_use"
    HAPPY = "happy"
    ALERT = "alert"
    SLEEPING = "sleeping"
    HATCH = "hatch"
    POKE = "poke"
    CODING = "coding"


SPRITES: Dict[str, Sprite] = {
    "idle_open": Sprite("idle_open", IDLE_OPEN),
    "idle_blink": Sprite("idle_blink", IDLE_BLINK),
    "thinking_a": Sprite("thinking_a", THINKING_A),
    "thinking_b": Sprite("thinking_b", THINKING_B),
    "thinking_c": Sprite("thinking_c", THINKING_C),
    "typing_up": Sprite("typing_up", TYPING_UP),
    "typing_down": Sprite("typing_down", TYPING_DOWN),
    "tool_use": Sprite("tool_use", TOOL_USE),
    "happy_a": Sprite("happy_a", HAPPY_A),
    "happy_b": Sprite("happy_b", HAPPY_B),
    "alert_a": Sprite("alert_a", ALERT_A),
    "alert_b": Sprite("alert_b", ALERT_B),
    "sleep_a": Sprite("sleep_a", SLEEP_A),
    "sleep_b": Sprite("sleep_b", SLEEP_B),
    "sleep_c": Sprite("sleep_c", SLEEP_C),
    "hatch": Sprite("hatch", HATCH),
    "idle_breathe": Sprite("idle_breathe", IDLE_BREATHE),
    "idle_look_l": Sprite("idle_look_l", IDLE_LOOK_L),
    "idle_look_r": Sprite("idle_look_r", IDLE_LOOK_R),
    "wave_up": Sprite("wave_up", WAVE_UP),
    "wave_up2": Sprite("wave_up2", WAVE_UP2),
    "bubble_1": Sprite("bubble_1", BUBBLE_1),
    "bubble_2": Sprite("bubble_2", BUBBLE_2),
    "bubble_pop": Sprite("bubble_pop", BUBBLE_POP),
    "stretch": Sprite("stretch", STRETCH),
}


# -------------------- conversion to RGB frames --------------------


def sprite_to_rgb_frame(sprite: Sprite) -> List[RGB]:
    """Flatten a sprite to a row-major list of 256 RGB tuples."""
    rgb: List[RGB] = []
    for row in sprite.rows:
        for ch in row:
            rgb.append(CLAWD_PALETTE.get(ch, (0, 0, 0)))
    if len(rgb) != 256:
        raise RuntimeError(f"sprite {sprite.name} did not flatten to 256 px: {len(rgb)}")
    return rgb


# -------------------- animations per state --------------------


@dataclass(frozen=True)
class IdleOpts:
    """Tunables for the idle loop, driven by user settings."""
    fidgets: bool = True       # look-around / wave / bubble / stretch
    frequency: float = 1.0     # multiplier on fidget probability (0 = never)
    blink: bool = True         # idle blinking


DEFAULT_IDLE = IdleOpts()

# Base per-cycle probability of each fidget (before the frequency multiplier).
_FIDGET_BASE = {"look": 0.10, "wave": 0.06, "bubble": 0.04, "stretch": 0.02}


def _idle_loop(idle: IdleOpts = DEFAULT_IDLE) -> List[Tuple[Sprite, int]]:
    """One randomized idle cycle. Called fresh each loop by the state machine, so
    successive cycles differ: a constant breathing bob, a decoupled + jittered
    blink most cycles, and a weighted-rare fidget (look-around / wave / bubble /
    stretch). Keeps Clawd from ever looking metronomic. `idle` gates blinking and
    scales (or disables) the fidgets per user settings."""
    seq: List[Tuple[Sprite, int]] = [
        (SPRITES["idle_open"], random.randint(1400, 2400)),    # inhale (held, varied)
        (SPRITES["idle_breathe"], random.randint(900, 1500)),  # exhale
    ]
    # Decoupled, jittered blink — most cycles, sometimes a double-blink.
    if idle.blink and random.random() < 0.7:
        seq.append((SPRITES["idle_open"], random.randint(300, 1100)))
        seq.append((SPRITES["idle_blink"], 120))
        if random.random() < 0.25:
            seq.append((SPRITES["idle_open"], 120))
            seq.append((SPRITES["idle_blink"], 110))

    # Weighted-rare fidget so the occasional one feels special.
    freq = idle.frequency if idle.fidgets else 0.0
    look = _FIDGET_BASE["look"] * freq
    wave = look + _FIDGET_BASE["wave"] * freq
    bubble = wave + _FIDGET_BASE["bubble"] * freq
    stretch = bubble + _FIDGET_BASE["stretch"] * freq
    r = random.random()
    if r < look:          # glance around
        seq += [(SPRITES["idle_look_l"], 620), (SPRITES["idle_open"], 240),
                (SPRITES["idle_look_r"], 620), (SPRITES["idle_open"], 300)]
    elif r < wave:        # wave hello
        seq += [(SPRITES["wave_up"], 230), (SPRITES["wave_up2"], 230),
                (SPRITES["wave_up"], 230), (SPRITES["wave_up2"], 230),
                (SPRITES["idle_open"], 200)]
    elif r < bubble:      # blow a bubble
        seq += [(SPRITES["bubble_1"], 420), (SPRITES["bubble_2"], 560),
                (SPRITES["bubble_pop"], 200), (SPRITES["idle_open"], 220)]
    elif r < stretch:     # big stretch
        seq += [(SPRITES["stretch"], 720), (SPRITES["idle_open"], 320)]
    return seq


def animation_for_state(state: State, idle: IdleOpts = DEFAULT_IDLE) -> List[Tuple[Sprite, int]]:
    """Return a list of (sprite, duration_ms) pairs that compose one loop."""
    if state == State.IDLE:
        return _idle_loop(idle)
    if state == State.THINKING:
        return [
            (SPRITES["thinking_a"], 220),
            (SPRITES["thinking_b"], 220),
            (SPRITES["thinking_c"], 220),
        ]
    if state == State.TYPING:
        return [
            (SPRITES["typing_up"], 160),
            (SPRITES["typing_down"], 160),
        ]
    if state == State.TOOL_USE:
        return [
            (SPRITES["tool_use"], 320),
            (SPRITES["idle_open"], 220),
        ]
    if state == State.HAPPY:
        return [
            (SPRITES["happy_a"], 380),
            (SPRITES["happy_b"], 280),
            (SPRITES["happy_a"], 380),
            (SPRITES["happy_b"], 280),
        ]
    if state == State.ALERT:
        return [
            (SPRITES["alert_a"], 200),
            (SPRITES["alert_b"], 200),
            (SPRITES["alert_a"], 200),
            (SPRITES["alert_b"], 200),
        ]
    if state == State.SLEEPING:
        return [
            (SPRITES["sleep_a"], 700),
            (SPRITES["sleep_b"], 700),
            (SPRITES["sleep_c"], 700),
        ]
    if state == State.HATCH:
        return [(SPRITES["hatch"], 2200)]
    if state == State.POKE:
        # startle (wide eyes) -> delighted (heart) -> grin
        return [
            (SPRITES["alert_b"], 260),
            (SPRITES["happy_a"], 520),
            (SPRITES["happy_b"], 420),
        ]
    if state == State.CODING:
        # Clawd at his laptop. Lazy import avoids a sprites import cycle.
        from divoom_pet.sprites.coding import DEFAULT_CODING_SCENE, SCENES
        return SCENES[DEFAULT_CODING_SCENE]
    raise ValueError(f"Unknown state: {state}")


# -------------------- preview rendering --------------------


def render_to_png(sprite: Sprite, path: str, scale: int = 16) -> None:
    """Save a PNG preview of a sprite, upscaled `scale`x for visibility."""
    from PIL import Image

    img = Image.new("RGB", (16, 16), (0, 0, 0))
    px = img.load()
    for y, row in enumerate(sprite.rows):
        for x, ch in enumerate(row):
            px[x, y] = CLAWD_PALETTE.get(ch, (0, 0, 0))
    if scale != 1:
        img = img.resize((16 * scale, 16 * scale), Image.NEAREST)
    img.save(path)


def render_all_previews(out_dir: str) -> None:
    import os
    os.makedirs(out_dir, exist_ok=True)
    for name, sprite in SPRITES.items():
        render_to_png(sprite, os.path.join(out_dir, f"{name}.png"))


if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "previews"
    render_all_previews(out_dir)
    print(f"wrote {len(SPRITES)} sprite previews to {out_dir}/")
