"""User settings for Clawd — persisted as JSON at ~/.clawd/config.json.

This is the single source of truth for the daemon. The menu-bar app and the
`clawd config` CLI edit it (directly, or via the daemon's POST /config endpoint),
and the daemon applies changes live where it can.

Config is immutable: every "change" produces a new Config via `merged()`, so there
are no hidden in-place mutations. Values are clamped to safe ranges on load.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger("config")

CONFIG_PATH = Path.home() / ".clawd" / "config.json"


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class DeviceCfg:
    mac: Optional[str] = None
    channel: int = 2


@dataclass(frozen=True)
class SoundsCfg:
    enabled: bool = True
    volume: float = 0.6              # 0..1, scales synthesized chirps
    audio_device: str = "DitooPro"   # output device name substring
    theme: str = "marimba"           # chirp theme: marimba/music_box/bubbly/chip


@dataclass(frozen=True)
class VoiceCfg:
    babble: bool = True              # occasional chiptune "muttering" while thinking
    spoken_lines: bool = True        # TTS "big moment" lines (Hi! I'm Clawd / All done!)
    tts_voice: Optional[str] = None  # None = auto-pick a nice system voice


@dataclass(frozen=True)
class MicCfg:
    enabled: bool = True             # clap detection (uses the Mac mic)
    clap_floor: float = 0.06         # RMS floor below which nothing counts
    clap_rise: float = 4.0           # how many x over floor a clap must peak
    double_window: float = 0.55      # seconds; two claps within this = double-clap


@dataclass(frozen=True)
class AnimationsCfg:
    brightness: int = 70             # 0..100 display brightness
    idle_fidgets: bool = True        # look-around / wave / bubble / stretch
    fidget_frequency: float = 1.0    # multiplier on fidget probability (0 = none)
    blink: bool = True               # idle blinking


@dataclass(frozen=True)
class SleepCfg:
    idle_to_sleep_seconds: float = 240.0  # nap after this long with no activity


@dataclass(frozen=True)
class Config:
    device: DeviceCfg = field(default_factory=DeviceCfg)
    sounds: SoundsCfg = field(default_factory=SoundsCfg)
    voice: VoiceCfg = field(default_factory=VoiceCfg)
    mic: MicCfg = field(default_factory=MicCfg)
    animations: AnimationsCfg = field(default_factory=AnimationsCfg)
    sleep: SleepCfg = field(default_factory=SleepCfg)

    # ---------- construction ----------

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Config":
        """Build a Config from a (possibly partial / untrusted) dict. Unknown keys
        are ignored, missing keys fall back to defaults, then values are clamped."""
        data = data or {}
        return cls(
            device=_section(DeviceCfg, data.get("device")),
            sounds=_section(SoundsCfg, data.get("sounds")),
            voice=_section(VoiceCfg, data.get("voice")),
            mic=_section(MicCfg, data.get("mic")),
            animations=_section(AnimationsCfg, data.get("animations")),
            sleep=_section(SleepCfg, data.get("sleep")),
        ).normalized()

    def normalized(self) -> "Config":
        """Return a copy with every value coerced into its safe range."""
        return replace(
            self,
            device=replace(self.device, channel=int(self.device.channel)),
            sounds=replace(self.sounds, volume=_clamp(float(self.sounds.volume), 0.0, 1.0)),
            mic=replace(
                self.mic,
                clap_floor=_clamp(float(self.mic.clap_floor), 0.0, 1.0),
                clap_rise=_clamp(float(self.mic.clap_rise), 1.0, 50.0),
                double_window=_clamp(float(self.mic.double_window), 0.2, 2.0),
            ),
            animations=replace(
                self.animations,
                brightness=int(_clamp(int(self.animations.brightness), 0, 100)),
                fidget_frequency=_clamp(float(self.animations.fidget_frequency), 0.0, 3.0),
            ),
            sleep=replace(
                self.sleep,
                idle_to_sleep_seconds=_clamp(float(self.sleep.idle_to_sleep_seconds), 10.0, 36000.0),
            ),
        )

    def merged(self, partial: Optional[Dict[str, Any]]) -> "Config":
        """Deep-merge a partial dict (one or more sections, any subset of keys) over
        this config and return a new, normalized Config."""
        base = self.to_dict()
        for section, values in (partial or {}).items():
            if section in base and isinstance(values, dict):
                base[section].update(values)
        return Config.from_dict(base)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # ---------- persistence ----------

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        p = Path(path)
        if not p.exists():
            return cls.from_dict({})
        try:
            return cls.from_dict(json.loads(p.read_text()))
        except (OSError, json.JSONDecodeError) as e:
            log.warning("config load failed (%s); using defaults", e)
            return cls.from_dict({})

    def save(self, path: Path = CONFIG_PATH) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2) + "\n")


def _section(cls, data: Any):
    """Build a section dataclass from a dict, ignoring unknown keys."""
    if not isinstance(data, dict):
        return cls()
    known = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in known})


# Settings that the daemon cannot apply live — changing them requires a restart.
NEEDS_RESTART = ("device.mac", "device.channel", "sounds.audio_device")
