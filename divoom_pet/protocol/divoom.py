"""Pure Divoom Ditoo packet builder.

Reverse-engineered protocol references:
- https://github.com/d03n3rfr1tz3/hass-divoom (Python reference, GPL)
- https://github.com/RomRider/node-divoom-timebox-evo/blob/0.3.0/PROTOCOL.md
- https://andreas-mausch.de/blog/2023-08-14-divoom-ditoo-pro/

No I/O happens here. Each function returns `bytes` ready to be framed for stdin
of the Swift `ditoo-bridge` (which expects `<2-byte LE length><payload>`).

Ditoo specifics:
- 16x16 screen
- chunksize = 200 for multi-frame animations
- escape_payload = False (no 0x03 escaping needed)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

RGB = Tuple[int, int, int]

SCREEN_SIZE = 16
PIXELS_PER_FRAME = SCREEN_SIZE * SCREEN_SIZE  # 256
CHUNK_SIZE = 200

# Command IDs (subset; full list in hass-divoom)
CMD_SET_VOLUME = 0x08
CMD_SET_PLAYSTATE = 0x0A
CMD_SET_DATE_TIME = 0x18
CMD_SET_LIGHTNESS = 0x32
CMD_SET_IMAGE = 0x44
CMD_SET_VIEW = 0x45
CMD_GET_VIEW = 0x46
CMD_SET_ANIMATION_FRAME = 0x49
CMD_SET_BRIGHTNESS = 0x74
CMD_SET_DESIGN = 0xBD


# -------------------- low-level packet framing --------------------


def _checksum(payload: bytes) -> bytes:
    total = sum(payload)
    # 4 bytes if sum overflows 2-byte field, else 2 bytes
    return total.to_bytes(4 if total >= 65535 else 2, "little")


def _wrap_message(payload: bytes) -> bytes:
    """Wrap an inner payload in the Divoom envelope: 0x01 | payload | checksum | 0x02.

    Ditoo doesn't escape payload bytes (escapePayload = False on this device family).
    """
    return b"\x01" + payload + _checksum(payload) + b"\x02"


def build_command(command: int, args: bytes = b"") -> bytes:
    """Build a single framed command ready to be written to the SPP channel."""
    length = len(args) + 3  # length includes itself (2 bytes) and command byte
    inner = length.to_bytes(2, "little") + bytes([command]) + args
    return _wrap_message(inner)


# -------------------- pixel encoding --------------------


def _quantize(rgb_pixels: Sequence[RGB]) -> Tuple[List[RGB], List[int]]:
    """Build a palette + per-pixel index list from a flat list of 256 RGB tuples."""
    palette: List[RGB] = []
    indices: List[int] = []
    seen: dict = {}
    for px in rgb_pixels:
        idx = seen.get(px)
        if idx is None:
            idx = len(palette)
            palette.append(px)
            seen[px] = idx
        indices.append(idx)
    return palette, indices


def _pack_pixels(palette: Sequence[RGB], indices: Sequence[int]) -> bytes:
    """Bit-pack pixel indices using ceil(log2(palette_size)) bits per pixel.

    Per the documented Divoom format: each index is written LSB-first, bits are
    concatenated, then chunked into 8-bit bytes (also LSB-first within each byte).
    """
    n_colors = max(1, len(palette))
    bpp = max(1, math.ceil(math.log2(n_colors)) if n_colors > 1 else 1)
    bits = []
    for idx in indices:
        for bit in range(bpp):
            bits.append((idx >> bit) & 1)
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i + 8]
        # LSB-first reassembly
        byte = 0
        for j, b in enumerate(chunk):
            byte |= (b & 1) << j
        out.append(byte)
    return bytes(out)


def _encode_frame(palette: Sequence[RGB], indices: Sequence[int],
                  duration_ms: int = 0, multi_frame: bool = False) -> bytes:
    """Encode a single frame's body (palette + pixel data + duration header)."""
    time_code = duration_ms.to_bytes(2, "little") if multi_frame else b"\x00\x00"
    palette_flag = b"\x00"  # Ditoo (16x16) uses 0x00; Pixoo-Max uses 0x03
    color_count = len(palette)
    if color_count >= PIXELS_PER_FRAME:
        color_count = 0  # protocol quirk: 0 means "as many as fit"
    color_count_b = bytes([color_count])
    palette_b = b"".join(bytes([r, g, b]) for (r, g, b) in palette)
    pixels_b = _pack_pixels(palette, indices)
    return time_code + palette_flag + color_count_b + palette_b + pixels_b


def _wrap_frame_for_stream(frame_body: bytes) -> bytes:
    """Prepend the AA + length header that the Divoom frame stream expects."""
    frame_length = len(frame_body) + 3  # +3 to include this length field + AA
    return b"\xAA" + frame_length.to_bytes(2, "little") + frame_body


# -------------------- public command builders --------------------


def build_set_brightness(value: int) -> bytes:
    value = max(0, min(100, int(value)))
    return build_command(CMD_SET_BRIGHTNESS, bytes([value]))


def build_set_image_from_rgb(rgb_pixels: Sequence[RGB]) -> bytes:
    """Push a single 16x16 frame (256 RGB tuples, row-major top-left first)."""
    if len(rgb_pixels) != PIXELS_PER_FRAME:
        raise ValueError(f"Expected {PIXELS_PER_FRAME} pixels, got {len(rgb_pixels)}")
    palette, indices = _quantize(rgb_pixels)
    frame_body = _encode_frame(palette, indices, duration_ms=0, multi_frame=False)
    aa_frame = _wrap_frame_for_stream(frame_body)
    # Single-image framepart uses a fixed [0x00, 0x0A, 0x0A, 0x04] header
    framepart = b"\x00\x0A\x0A\x04" + aa_frame
    return build_command(CMD_SET_IMAGE, framepart)


def build_set_animation_from_rgb_frames(
    frames: Iterable[Tuple[Sequence[RGB], int]],
) -> List[bytes]:
    """Push a multi-frame animation. Returns N command packets to send sequentially.

    `frames` is an iterable of (256-pixel list, duration_ms) pairs.
    """
    frames_list = list(frames)
    encoded_frames = bytearray()
    frame_count = len(frames_list)
    for pixels, duration in frames_list:
        if len(pixels) != PIXELS_PER_FRAME:
            raise ValueError("Each frame must have exactly 256 RGB pixels")
        palette, indices = _quantize(pixels)
        body = _encode_frame(palette, indices, duration_ms=duration, multi_frame=True)
        encoded_frames.extend(_wrap_frame_for_stream(body))

    total_size = len(encoded_frames)
    commands: List[bytes] = []
    index = 0
    for chunk_start in range(0, total_size, CHUNK_SIZE):
        chunk = bytes(encoded_frames[chunk_start:chunk_start + CHUNK_SIZE])
        # Multi-frame framepart header: total-size LE u16 + chunk-index u8
        header = total_size.to_bytes(2, "little") + index.to_bytes(1, "little")
        commands.append(build_command(CMD_SET_ANIMATION_FRAME, header + chunk))
        index += 1
    if not commands:
        raise ValueError("No animation frames provided")
    return commands


def build_set_view_clock(face: int = 0, color: RGB = (255, 255, 255)) -> bytes:
    """Switch the Ditoo back to a built-in clock face (handy reset/finale state)."""
    args = bytes([
        0x00,           # subcommand: clock view
        0x00,           # 12-hour
        face & 0xFF,    # clock face id (0..15)
        0x01,           # clock activated
        0x00,           # weather off
        0x00,           # temp off
        0x00,           # calendar off
    ]) + bytes(color)
    return build_command(CMD_SET_VIEW, args)


# -------------------- Swift bridge framing --------------------


def to_bridge_frame(packet: bytes) -> bytes:
    """Wrap a packet with the 2-byte LE length prefix the Swift bridge expects on stdin."""
    if len(packet) > 0xFFFF:
        raise ValueError("Packet too large for bridge framing")
    return len(packet).to_bytes(2, "little") + packet


def bridge_close_frame() -> bytes:
    """Special zero-length frame that asks the bridge to close cleanly."""
    return b"\x00\x00"


# -------------------- compat alias --------------------


@dataclass(frozen=True)
class DivoomProtocol:
    """Tiny convenience holder so callers can use one object instead of free fns."""
    screen_size: int = SCREEN_SIZE
    chunk_size: int = CHUNK_SIZE

    def set_brightness(self, value: int) -> bytes:
        return build_set_brightness(value)

    def set_image(self, rgb_pixels: Sequence[RGB]) -> bytes:
        return build_set_image_from_rgb(rgb_pixels)

    def set_animation(self, frames: Iterable[Tuple[Sequence[RGB], int]]) -> List[bytes]:
        return build_set_animation_from_rgb_frames(frames)

    def set_clock(self, face: int = 0, color: RGB = (255, 255, 255)) -> bytes:
        return build_set_view_clock(face, color)
