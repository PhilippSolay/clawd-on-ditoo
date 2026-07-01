"""Bored-idle scenes for Clawd — what a restless crab gets up to before napping.

After a stretch of no activity Clawd doesn't just nap. First he gets *restless*.
Sometimes he hits the (sea)floor gym — jump rope, push-ups, dumbbell presses,
jumping jacks, and (a crab being a boxer with two built-in gloves) shadowboxing.
Other times he winds down instead: a seated meditation, a cup of tea, some yoga.
He rolls the dice each loop, so you never know which. A few minutes of that and
*then* he naps.

Same char-grid + palette system as clawd.py. Each scene is a list of
(Sprite, duration_ms). One "rep" is usually two frames; scenes repeat the rep a
few times so a single loop reads as a short beat before he switches activity.
"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

from .clawd import CLAWD_PALETTE, Sprite, _canvas

# Sports palette (uppercase keys so they never collide with Clawd's lowercase set).
CLAWD_PALETTE["R"] = (232, 208, 150)   # jump-rope cord (warm sisal)
CLAWD_PALETTE["W"] = (84, 90, 105)     # cold iron — dumbbell bar + plates
CLAWD_PALETTE["B"] = (120, 180, 230)   # a bead of sweat / effort splash
CLAWD_PALETTE["M"] = (150, 120, 200)   # zen mat / meditation cushion (calm violet)
CLAWD_PALETTE["T"] = (168, 96, 60)     # steeped tea in the cup
# (reuses 'r' = red for boxing gloves, 'a' = Anthropic yellow for effort/zen sparks,
#  'c'/'w' for the teacup + steam + breathing aura, '-' for peaceful closed eyes)


def _reps(*frames: Tuple[Sprite, int], times: int = 3) -> List[Tuple[Sprite, int]]:
    """Repeat a short rep `times` so one loop is a small set, not a single twitch."""
    out: List[Tuple[Sprite, int]] = []
    for _ in range(times):
        out.extend(frames)
    return out


# ---------- 1. jump rope ----------
# Classic two-beat skip: rope arcs OVER the head while the crab is grounded, then
# swings UNDER the feet while he hops up a pixel. Pinchers hold the cord at the
# shell line; the sides of the rope hide behind his body (just like the real thing).

JUMPROPE_OVER = _canvas([
    "..RRRRRRRRRRRR..",   # rope apex, up over the head
    "R...k......k...R",   # cord runs down the far edges; clean face beneath
    "R...o......o...R",
    "R...o......o...R",
    "R.ooooooooooo.R.",   # cord ends land in the raised pinchers (shell corners)
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",   # feet planted on the ground
    "..o.o.oo.oo.o.o.",
    "..o...o..o...o..",
    "................",
    "................",
    "................",
    "................",
])

JUMPROPE_UNDER = _canvas([
    "................",
    "....k......k....",   # crab hopped up a pixel; rope has left the top
    "....o......o....",
    "..ooooooooooo...",
    "RooooohoooohoooR",   # pinchers still gripping the cord ends
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o.oo.oo.o.o.",   # feet tucked up for the hop
    "R.o.o.oo.oo.o.oR",   # cord tails drop back down the sides
    ".R..........R...",
    "..RRRRRRRRRR....",   # rope arc sweeping UNDER the feet
    "................",
    "................",
    "................",
    "................",
])


# ---------- 2. push-ups ----------
# Crab goes horizontal and pumps: arms extended (up), then chest to the floor
# (down). A bead of sweat flicks off on the down-beat. A dim floor line grounds it.

PUSHUP_UP = _canvas([
    "................",
    "..............B.",   # sweat flicking off
    "................",
    "....k......k....",   # arms locked out — shell held high off the deck
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".o.o.oo.oo.o.o..",   # long straight support posts (claws + legs)
    ".o.o.oo.oo.o.o..",
    ".o.o.oo.oo.o.o..",
    ".o...o....o...o.",   # planted on the deck
    "................",
    "dddddddddddddddd",   # floor
    "................",
    "................",
])

PUSHUP_DOWN = _canvas([
    "................",
    "..B.............",   # sweat on the other side
    "................",
    "................",
    "................",
    "................",
    "................",
    "....k......k....",   # dipped ~4px: shell lowered right to the deck
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    "oo.oo..oo..oo.oo",   # arms folded out, chest kissing the floor
    "dddddddddddddddd",   # floor
    "................",
    "................",
])


# ---------- 3. dumbbell press ----------
# An iron bar travels from the waist (racked) to locked-out overhead. Plates on
# the ends read as the weight; the pinchers press straight up.

WEIGHTS_RACK = _canvas([
    "................",
    "....k......k....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    ".o.o.oo.oo.o.o..",
    "WWWWWWWWWWWWWWWW",   # bar racked low across the body
    "WW..........WW..",   # end plates
    "................",
    "................",
    "................",
    "................",
])

WEIGHTS_PRESS = _canvas([
    "WW..........WW..",   # end plates, up top
    "WWWWWWWWWWWWWWWW",   # bar pressed overhead
    "..o..k..k..o....",   # pinchers locked out; eyes below the bar
    "..o..o..o..o....",   # arms extended straight up
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


# ---------- 4. jumping jacks ----------
# Closed (arms in, legs together) snaps to open (star: pinchers thrown up-out,
# legs spread wide). The silhouette change is the whole read.

JACKS_CLOSED = _canvas([
    "................",
    "....k......k....",
    "....o......o....",
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "...oo....oo.....",   # arms tucked in
    "....o....o......",
    "....oo..oo......",   # legs together
    ".....o..o.......",
    "................",
    "................",
    "................",
])

JACKS_OPEN = _canvas([
    "oo..k......k..oo",   # pinchers thrown up into the star
    ".o..o......o..o.",
    "..o.o......o.o..",
    "...ooooooooooo..",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..o.o....o.o....",
    ".o..o....o..o...",   # legs kicked wide
    "o...o....o...o..",
    "................",
    "................",
    "................",
    "................",
])


# ---------- 5. shadowboxing ----------
# A crab is a boxer that came pre-equipped. Red gloves jab left, then right; the
# off-claw stays up as a guard by the eye. Quick alternating one-twos.

BOX_LEFT = _canvas([
    "................",
    "....k......k....",
    "....o.....oo....",   # right pincher up on guard
    "........o.o.....",
    "rr..ooooooo.o...",   # LEFT glove jabs out, arm back to the shell
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

BOX_RIGHT = _canvas([
    "................",
    "....k......k....",
    "....oo.....o....",   # left pincher up on guard
    ".....o.o........",
    "...o.ooooooo..rr",   # RIGHT glove jabs out
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


# ---------- 6. meditation ----------
# Seated on a cushion, eyes shut, a breathing aura that swells on the inhale. The
# calm counterweight to the boxing. Legs tuck into a stable base; a zen spark lifts.

MEDITATE_OUT = _canvas([   # exhale — aura drawn in, spark low
    "................",
    "................",
    "....-......-....",   # peaceful closed eyes
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..ooooooooooo...",   # legs folded into a seated base
    "..o.oo..oo.o....",   # crossed legs
    "..MMMMMMMMMMM...",   # meditation cushion
    "...MMMMMMMMM....",
    "................",
    "................",
    "................",
])

MEDITATE_IN = _canvas([   # inhale — aura swells, a zen spark rises
    ".......a........",   # zen spark
    "....c.....c.....",   # aura, expanded
    "....-......-....",   # eyes still shut
    "...co......oc...",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "..ooooooooooo...",
    "..o.oo..oo.o....",
    "..MMMMMMMMMMM...",
    "...MMMMMMMMM....",
    "....c.....c.....",   # aura below
    "................",
    "................",
])


# ---------- 7. a cup of tea ----------
# Content eyes, a little cup with steeped tea, steam curling up. He lifts it for a
# sip on the second beat; the steam drifts to sell the warmth.

TEA_HOLD = _canvas([   # cup held at the chest, first curl of steam
    "...........c....",   # steam
    "..........c.....",
    "....k......k....",   # content, open eyes
    "....o......o....",
    "..ooooooooooo...",
    "ooooohoooohoooo.",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooccc..",   # right claw brings a cup up (rim)
    "..o.o.oo.o.cTc..",   # steeped tea inside
    "..o.o.oo.o.ccc..",   # cup base
    "..o...o..o..c...",   # little handle / legs
    "................",
    "................",
    "................",
    "................",
])

TEA_SIP = _canvas([   # cup tipped up to the face for a sip, steam risen + spread
    ".........c.c....",   # steam, higher and spread
    "..........c.....",
    "....k....ccc....",   # cup raised to the mouth
    "....o....cTc....",   # sipping
    "..oooooooccco...",   # arm lifts the cup up to the face
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


# ---------- 8. yoga ----------
# Tree pose: pinchers pressed together overhead, balanced on a tucked stance atop
# a mat, swaying gently to hold the balance. Eyes ride on the shell so the crown
# is free for the prayer.

YOGA_TREE = _canvas([   # centered, prayer straight up
    ".......a........",   # a calm spark
    "......ooo.......",   # pinchers pressed together (prayer)
    ".......o........",
    ".......o........",
    "..ooooooooooo...",
    "ooookoooookooo..",   # serene eyes on the shell front
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "......ooo.......",   # legs drawn together for balance
    ".......o........",   # one supporting leg
    ".......o........",
    "..MMMMMMMMMM....",   # yoga mat
    "................",
    "................",
    "................",
])

YOGA_SWAY = _canvas([   # gentle sway to hold the balance
    "......a.........",   # spark drifts
    ".....ooo........",   # prayer leans
    "......o.........",
    "......o.........",
    "..ooooooooooo...",
    "ooookoooookooo..",
    "oooooooooooooooo",
    "oodddoooodddoooo",
    ".ooooooooooooooo",
    "......ooo.......",
    ".......o........",   # supporting leg
    "........o.......",   # a wobble
    "..MMMMMMMMMM....",   # mat
    "................",
    "................",
    "................",
])


# ---------- registry ----------

SPORT_SPRITES: Dict[str, Sprite] = {
    "jumprope_over": Sprite("jumprope_over", JUMPROPE_OVER),
    "jumprope_under": Sprite("jumprope_under", JUMPROPE_UNDER),
    "pushup_up": Sprite("pushup_up", PUSHUP_UP),
    "pushup_down": Sprite("pushup_down", PUSHUP_DOWN),
    "weights_rack": Sprite("weights_rack", WEIGHTS_RACK),
    "weights_press": Sprite("weights_press", WEIGHTS_PRESS),
    "jacks_closed": Sprite("jacks_closed", JACKS_CLOSED),
    "jacks_open": Sprite("jacks_open", JACKS_OPEN),
    "box_left": Sprite("box_left", BOX_LEFT),
    "box_right": Sprite("box_right", BOX_RIGHT),
    "meditate_out": Sprite("meditate_out", MEDITATE_OUT),
    "meditate_in": Sprite("meditate_in", MEDITATE_IN),
    "tea_hold": Sprite("tea_hold", TEA_HOLD),
    "tea_sip": Sprite("tea_sip", TEA_SIP),
    "yoga_tree": Sprite("yoga_tree", YOGA_TREE),
    "yoga_sway": Sprite("yoga_sway", YOGA_SWAY),
}

# Named sport animations: name -> list of (Sprite, duration_ms). Each is a short set.
SCENES: Dict[str, List[Tuple[Sprite, int]]] = {
    "jumprope": _reps((SPORT_SPRITES["jumprope_over"], 200),
                      (SPORT_SPRITES["jumprope_under"], 200), times=4),
    "pushups": _reps((SPORT_SPRITES["pushup_up"], 300),
                     (SPORT_SPRITES["pushup_down"], 300), times=3),
    "weights": _reps((SPORT_SPRITES["weights_rack"], 340),
                     (SPORT_SPRITES["weights_press"], 420), times=3),
    "jumpingjacks": _reps((SPORT_SPRITES["jacks_closed"], 230),
                          (SPORT_SPRITES["jacks_open"], 230), times=4),
    "boxing": _reps((SPORT_SPRITES["box_left"], 190),
                    (SPORT_SPRITES["box_right"], 190), times=4),
    # Chill wind-downs — slower beats, gentler cadence.
    "meditate": _reps((SPORT_SPRITES["meditate_out"], 900),
                      (SPORT_SPRITES["meditate_in"], 900), times=2),
    "tea": _reps((SPORT_SPRITES["tea_hold"], 700),
                 (SPORT_SPRITES["tea_sip"], 850), times=2),
    "yoga": _reps((SPORT_SPRITES["yoga_tree"], 780),
                  (SPORT_SPRITES["yoga_sway"], 640), times=2),
}

# The order Clawd cycles through when he can't sit still (also the GIF gallery order).
SPORT_ORDER = ["jumprope", "pushups", "weights", "jumpingjacks", "boxing",
               "meditate", "tea", "yoga"]


def random_sport() -> List[Tuple[Sprite, int]]:
    """Pick one activity at random — the SPORTY state calls this fresh each loop, so
    a bored Clawd does one thing (a workout or a wind-down), then rolls into another."""
    return SCENES[random.choice(SPORT_ORDER)]


# How long a quick idle "peek" of an activity should last (see quick_activity).
_QUICK_TASTE_MS = 1600


def quick_activity() -> List[Tuple[Sprite, int]]:
    """A brief taste of one activity — a couple of jumping jacks, a sip of tea — sized
    to ~1.6s, for mixing into the *normal* idle loop. It's the amuse-bouche; the full
    SPORTY state (after a minute idle) is the whole meal."""
    scene = SCENES[random.choice(SPORT_ORDER)]
    rep = scene[:2]                                  # one rep = the two base frames
    beat = sum(ms for _, ms in rep) or 1
    reps = max(1, round(_QUICK_TASTE_MS / beat))
    return rep * reps
