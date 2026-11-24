"""Unit tests for tools/bps.py (no ROM needed)."""
import os
import random
import sys
import unittest
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import bps  # noqa: E402


class BPSTests(unittest.TestCase):
    def roundtrip(self, src, tgt):
        patch = bps.create(src, tgt)
        self.assertEqual(bps.apply(src, patch), tgt)
        return patch

    def test_numbers(self):
        for n in [0, 1, 127, 128, 255, 16383, 16384, 2**24, 2**32 + 7]:
            enc = bps.encode_number(n)
            self.assertEqual(bps.decode_number(enc, 0), (n, len(enc)))

    def test_identical(self):
        data = random.Random(1).randbytes(50_000)
        self.assertLess(len(self.roundtrip(data, data)), 64)

    def test_small_edit(self):
        src = bytearray(random.Random(2).randbytes(100_000))
        tgt = bytearray(src)
        tgt[5000:5004] = b"\x00\x01\x02\x03"
        self.assertLess(len(self.roundtrip(bytes(src), bytes(tgt))), 200)

    def test_insertion_shifts_data(self):
        """Code inserted mid-ROM shifts everything after it, like a real linker change."""
        src = random.Random(3).randbytes(200_000)
        tgt = src[:70_000] + b"NEW CODE" * 5 + src[70_000:-40]
        self.assertLess(len(self.roundtrip(src, tgt)), 400)

    def test_deletion_and_growth(self):
        src = random.Random(4).randbytes(30_000)
        self.roundtrip(src, src[:10_000] + src[12_000:] + b"\xff" * 5000)
        self.roundtrip(src, b"")
        self.roundtrip(b"", src[:100])

    def test_rejects_wrong_source(self):
        src = random.Random(5).randbytes(10_000)
        patch = bps.create(src, src[:5000] + b"x" + src[5001:])
        with self.assertRaises(bps.BPSError):
            bps.apply(b"y" + src[1:], patch)

    def test_rejects_damaged_patch(self):
        src = random.Random(6).randbytes(10_000)
        patch = bytearray(bps.create(src, src[::-1]))
        patch[20] ^= 0xFF
        with self.assertRaises(bps.BPSError):
            bps.apply(src, bytes(patch))

    def test_target_copy_decoding(self):
        """Hand-built patch using TargetCopy (our encoder never emits it; Floating IPS does)."""
        body = bytearray(b"BPS1") + bps.encode_number(0) + bps.encode_number(6) + bps.encode_number(0)
        body += bps.encode_number(((2 - 1) << 2) | bps.TARGET_READ) + b"ab"
        body += bps.encode_number(((4 - 1) << 2) | bps.TARGET_COPY) + bps.encode_number(0)
        body += zlib.crc32(b"").to_bytes(4, "little") + zlib.crc32(b"ababab").to_bytes(4, "little")
        body += zlib.crc32(body).to_bytes(4, "little")
        self.assertEqual(bps.apply(b"", bytes(body)), b"ababab")


if __name__ == "__main__":
    unittest.main()
