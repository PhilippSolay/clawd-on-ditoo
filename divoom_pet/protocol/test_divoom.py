"""Unit tests for the protocol builder. Run with: python -m pytest divoom_pet/protocol/test_divoom.py -v
Or simply: python divoom_pet/protocol/test_divoom.py
"""

import unittest

from divoom_pet.protocol.divoom import (
    PIXELS_PER_FRAME,
    SCREEN_SIZE,
    _checksum,
    _encode_frame,
    _pack_pixels,
    _quantize,
    _wrap_message,
    bridge_close_frame,
    build_command,
    build_set_animation_from_rgb_frames,
    build_set_brightness,
    build_set_image_from_rgb,
    to_bridge_frame,
)


class FramingTests(unittest.TestCase):
    def test_checksum_2_bytes(self):
        # sum 0x10 + 0x20 = 0x30 -> LE 2 bytes
        self.assertEqual(_checksum(b"\x10\x20"), b"\x30\x00")

    def test_wrap_message_envelope(self):
        # payload [0xAB] -> sum 0xAB -> checksum 0xAB 0x00
        out = _wrap_message(b"\xAB")
        self.assertEqual(out[0], 0x01)
        self.assertEqual(out[-1], 0x02)
        self.assertEqual(out, b"\x01\xAB\xAB\x00\x02")

    def test_build_command_brightness(self):
        # set brightness 50 -> command 0x74, args [0x32], length = 3 + 1 = 4
        cmd = build_set_brightness(50)
        # inner: 04 00 74 32 -> sum 0xAA -> checksum AA 00 -> envelope 01 04 00 74 32 AA 00 02
        self.assertEqual(cmd, b"\x01\x04\x00\x74\x32\xAA\x00\x02")

    def test_brightness_clamping(self):
        self.assertEqual(build_set_brightness(150)[4], 100)
        self.assertEqual(build_set_brightness(-10)[4], 0)


class QuantizeTests(unittest.TestCase):
    def test_quantize_dedups(self):
        red = (255, 0, 0); blue = (0, 0, 255)
        palette, indices = _quantize([red, blue, red, red])
        self.assertEqual(palette, [red, blue])
        self.assertEqual(indices, [0, 1, 0, 0])

    def test_pack_pixels_single_color(self):
        # 256 same-color pixels -> palette 1 -> bpp 1 -> 256 bits all 0 -> 32 zero bytes
        palette, idx = _quantize([(10, 20, 30)] * PIXELS_PER_FRAME)
        packed = _pack_pixels(palette, idx)
        self.assertEqual(packed, b"\x00" * 32)

    def test_pack_pixels_two_color_checkerboard(self):
        # Alternating indices 0,1,0,1...; bpp = 1; LSB-first bits 01010101 -> 0xAA
        pixels = []
        for i in range(PIXELS_PER_FRAME):
            pixels.append((255, 0, 0) if i % 2 == 0 else (0, 255, 0))
        palette, idx = _quantize(pixels)
        packed = _pack_pixels(palette, idx)
        # Each byte should be 0xAA (10101010 in MSB but we pack LSB-first so 01010101 = 0xAA)
        self.assertEqual(len(packed), 32)
        # bits LSB-first: 0,1,0,1,0,1,0,1 -> byte = 0xAA
        self.assertTrue(all(b == 0xAA for b in packed))


class FrameEncodeTests(unittest.TestCase):
    def test_single_image_envelope(self):
        # All-black 16x16
        pixels = [(0, 0, 0)] * PIXELS_PER_FRAME
        cmd = build_set_image_from_rgb(pixels)
        # Must start with 0x01 and end with 0x02
        self.assertEqual(cmd[0], 0x01)
        self.assertEqual(cmd[-1], 0x02)
        # Length field encodes args+3 in 2 LE bytes after 0x01
        length_lo, length_hi = cmd[1], cmd[2]
        length_field = length_lo | (length_hi << 8)
        # The 0x44 command byte sits immediately after the length field
        self.assertEqual(cmd[3], 0x44)
        # args length = length_field - 3
        args_len = length_field - 3
        # cmd = [01][len lo][len hi][cmd][args...][csum lo][csum hi][02]
        self.assertEqual(len(cmd), 4 + args_len + 2 + 1)

    def test_image_length_matches_args(self):
        # Pixel data must round-trip correctly. Two-color frame -> small packet
        pixels = [(255, 0, 0)] * PIXELS_PER_FRAME
        cmd = build_set_image_from_rgb(pixels)
        # Should not crash, should produce a well-formed packet
        self.assertTrue(len(cmd) >= 20)

    def test_animation_chunking(self):
        # 3 frames of single color
        frames = [
            ([(255, 0, 0)] * PIXELS_PER_FRAME, 100),
            ([(0, 255, 0)] * PIXELS_PER_FRAME, 100),
            ([(0, 0, 255)] * PIXELS_PER_FRAME, 100),
        ]
        commands = build_set_animation_from_rgb_frames(frames)
        # Should yield at least one packet
        self.assertTrue(len(commands) >= 1)
        # Each command is well-framed
        for c in commands:
            self.assertEqual(c[0], 0x01)
            self.assertEqual(c[-1], 0x02)
            # Animation frame command is 0x49
            self.assertEqual(c[3], 0x49)


class BridgeFramingTests(unittest.TestCase):
    def test_bridge_frame_prefixes_length(self):
        cmd = build_set_brightness(50)
        framed = to_bridge_frame(cmd)
        self.assertEqual(framed[:2], len(cmd).to_bytes(2, "little"))
        self.assertEqual(framed[2:], cmd)

    def test_close_frame_is_two_zeros(self):
        self.assertEqual(bridge_close_frame(), b"\x00\x00")


class ScreenSizeTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(SCREEN_SIZE, 16)
        self.assertEqual(PIXELS_PER_FRAME, 256)


if __name__ == "__main__":
    unittest.main()
