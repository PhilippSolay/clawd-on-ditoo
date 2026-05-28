"""Divoom Ditoo protocol builder (pure, no I/O)."""

from .divoom import (
    DivoomProtocol,
    build_set_brightness,
    build_set_image_from_rgb,
    build_set_animation_from_rgb_frames,
    build_set_view_clock,
)

__all__ = [
    "DivoomProtocol",
    "build_set_brightness",
    "build_set_image_from_rgb",
    "build_set_animation_from_rgb_frames",
    "build_set_view_clock",
]
