"""Clawd sprite library — pixel art for the orange Anthropic crab."""

from .clawd import (
    CLAWD_PALETTE,
    DEFAULT_IDLE,
    SPRITES,
    IdleOpts,
    Sprite,
    State,
    animation_for_state,
    render_to_png,
    sprite_to_rgb_frame,
)

__all__ = [
    "CLAWD_PALETTE",
    "DEFAULT_IDLE",
    "SPRITES",
    "IdleOpts",
    "Sprite",
    "State",
    "animation_for_state",
    "render_to_png",
    "sprite_to_rgb_frame",
]
