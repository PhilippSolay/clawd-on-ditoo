"""Richer synthesis for Clawd's voice — warmer, more organic timbres than the bare
chiptune. Pure Python (zero deps), used at render time only (the daemon just plays
the cached WAVs).

Works in floating-point sample lists so effects can chain (additive → lowpass →
echo), then `pack()` clamps to the same 22050 Hz / mono / Int16 format the rest of
the sound cache uses. Master volume is read live from `sounds` at pack time.
"""

from __future__ import annotations

import math
import random
import struct
from typing import Callable, List, Sequence, Tuple

from . import sounds as _snd
from .sounds import SAMPLE_RATE, _env, note

Samples = List[float]
Voice = Callable[[float, float], Samples]  # (freq_hz, dur_s) -> samples


# -------------------- oscillators --------------------


def additive(freq: float, dur: float, partials: Sequence[Tuple[float, float]],
             attack: float = 0.004, decay: float = 0.5, detune_cents: float = 0.0,
             volume: float = 0.5) -> Samples:
    """Sum sine partials [(harmonic_ratio, amplitude), …] under an AD envelope.
    Fundamental + a few harmonics gives wood/mallet/bell timbres."""
    n = int(SAMPLE_RATE * dur)
    out = [0.0] * n
    if freq <= 0 or n == 0:
        return out
    norm = sum(a for _, a in partials) or 1.0
    spread = 2 ** (detune_cents / 1200.0)
    for ratio, amp in partials:
        f = freq * ratio * spread
        phase = 0.0
        scale = amp / norm
        for i in range(n):
            phase += f / SAMPLE_RATE
            out[i] += scale * math.sin(2 * math.pi * phase)
    for i in range(n):
        out[i] *= volume * _env(i, n, attack, decay)
    return out


def fm(freq: float, dur: float, ratio: float = 2.0, index: float = 2.0,
       attack: float = 0.004, decay: float = 0.5, volume: float = 0.5) -> Samples:
    """One-operator FM — cheap bell/electric-piano-ish tones."""
    n = int(SAMPLE_RATE * dur)
    out = [0.0] * n
    if freq <= 0 or n == 0:
        return out
    cph = mph = 0.0
    for i in range(n):
        mph += (freq * ratio) / SAMPLE_RATE
        cph += freq / SAMPLE_RATE
        sample = math.sin(2 * math.pi * cph + index * math.sin(2 * math.pi * mph))
        out[i] = sample * volume * _env(i, n, attack, decay)
    return out


def glide(f_start: float, f_end: float, dur: float, attack: float = 0.006,
          decay: float = 0.5, volume: float = 0.5) -> Samples:
    """A sine that slides exponentially from f_start to f_end — a "bloop"."""
    n = int(SAMPLE_RATE * dur)
    out = [0.0] * n
    if f_start <= 0 or f_end <= 0 or n == 0:
        return out
    phase = 0.0
    ratio = f_end / f_start
    for i in range(n):
        t = i / max(1, n - 1)
        f = f_start * (ratio ** t)
        phase += f / SAMPLE_RATE
        out[i] = math.sin(2 * math.pi * phase) * volume * _env(i, n, attack, decay)
    return out


# -------------------- effects --------------------


def lowpass(samples: Samples, alpha: float = 0.35) -> Samples:
    """One-pole lowpass — rounds off harsh high end. alpha 0..1 (higher = brighter)."""
    y = 0.0
    out = []
    for x in samples:
        y += alpha * (x - y)
        out.append(y)
    return out


def echo(samples: Samples, delay_s: float = 0.08, decay: float = 0.35,
         repeats: int = 2) -> Samples:
    """Feedback delay — a little air/sparkle. Extends the buffer for the tail."""
    d = max(1, int(SAMPLE_RATE * delay_s))
    out = list(samples) + [0.0] * (d * repeats)
    for r in range(1, repeats + 1):
        amp = decay ** r
        offset = d * r
        for i in range(len(samples)):
            out[i + offset] += samples[i] * amp
    return out


def silence(dur: float) -> Samples:
    return [0.0] * int(SAMPLE_RATE * dur)


# -------------------- composition --------------------


def render_gesture(notes: Sequence[Tuple[str, float]], voice: Voice,
                   gap: float = 0.0) -> Samples:
    """Render a melody (list of (note_name, dur_s)) through a voice function."""
    out: Samples = []
    for name, dur in notes:
        out.extend(voice(note(name), dur))
        if gap > 0:
            out.extend(silence(gap))
    return out


def pack(samples: Samples) -> bytes:
    """Clamp + scale by the live master volume → little-endian Int16 PCM bytes."""
    master = _snd.MASTER_VOLUME
    buf = bytearray()
    for s in samples:
        v = max(-1.0, min(1.0, s * master))
        buf.extend(struct.pack("<h", int(v * 32767)))
    return bytes(buf)
