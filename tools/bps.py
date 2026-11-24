#!/usr/bin/env python3
"""Create, apply and verify BPS patches (byuu/Near's beat format), with no dependencies.

Usage:
    bps.py create SOURCE TARGET PATCH   # writes PATCH, then re-applies it to prove it round-trips
    bps.py apply  SOURCE PATCH OUTPUT   # checks source/target/patch CRC32s
    bps.py info   PATCH

The encoder uses SourceRead for bytes unchanged at the same offset, SourceCopy for data that has
moved (code shifted by the linker), and TargetRead for genuinely new bytes. Patches made with it
apply in any standard BPS tool (Floating IPS, beat, Rom Patcher JS); scripts/build.sh checks every
patch with Floating IPS when it is built (scripts/build-flips.sh).
"""
import sys
import zlib

SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY = 0, 1, 2, 3
K = 16            # bytes hashed to find moved data
STRIDE = 8        # sample every STRIDE-th source position for the index
MIN_COPY = 24     # shortest moved run worth a SourceCopy
MIN_SAME = 8      # shortest same-offset run worth a SourceRead


class BPSError(Exception):
    pass


def encode_number(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def decode_number(data, pos):
    n, shift = 0, 1
    while True:
        if pos >= len(data):
            raise BPSError("truncated number")
        x = data[pos]
        pos += 1
        n += (x & 0x7F) * shift
        if x & 0x80:
            return n, pos
        shift <<= 7
        n += shift


def _match_len(a, ai, b, bi, limit):
    """Length of the common run a[ai:] == b[bi:], up to limit (chunked for speed)."""
    n = 0
    step = 4096
    while n < limit:
        s = min(step, limit - n)
        if a[ai + n:ai + n + s] == b[bi + n:bi + n + s]:
            n += s
            continue
        if step == 1:
            break
        step = max(1, step // 16)
    return n


def create(source, target, metadata=b""):
    src, tgt = bytes(source), bytes(target)
    index = {}
    for p in range(0, len(src) - K + 1, STRIDE):
        index.setdefault(src[p:p + K], p)

    out = bytearray(b"BPS1")
    out += encode_number(len(src)) + encode_number(len(tgt)) + encode_number(len(metadata)) + metadata
    pending = bytearray()      # TargetRead bytes not yet written
    src_rel = 0                # BPS relative source offset for SourceCopy

    def flush():
        if pending:
            out.extend(encode_number(((len(pending) - 1) << 2) | TARGET_READ))
            out.extend(pending)
            pending.clear()

    i, n = 0, len(tgt)
    while i < n:
        # 1. unchanged at the same offset
        if i < len(src):
            same = _match_len(src, i, tgt, i, min(len(src), n) - i)
            if same >= MIN_SAME or (same and i + same == n):
                flush()
                out.extend(encode_number(((same - 1) << 2) | SOURCE_READ))
                i += same
                continue
        # 2. moved data
        best_len, best_src, best_back = 0, 0, 0
        if i + K <= n:
            p = index.get(tgt[i:i + K])
            if p is not None:
                length = _match_len(src, p, tgt, i, min(len(src) - p, n - i))
                if length >= MIN_COPY:
                    back = 0
                    while back < len(pending) and p - back > 0 and src[p - back - 1] == pending[-1 - back]:
                        back += 1
                    best_len, best_src, best_back = length, p, back
        if best_len:
            if best_back:
                del pending[-best_back:]
            flush()
            start, length = best_src - best_back, best_len + best_back
            delta = start - src_rel
            out.extend(encode_number(((length - 1) << 2) | SOURCE_COPY))
            out.extend(encode_number((abs(delta) << 1) | (1 if delta < 0 else 0)))
            src_rel = start + length
            i += best_len
            continue
        # 3. new byte
        pending.append(tgt[i])
        i += 1
    flush()
    out += zlib.crc32(src).to_bytes(4, "little")
    out += zlib.crc32(tgt).to_bytes(4, "little")
    out += zlib.crc32(out).to_bytes(4, "little")
    return bytes(out)


def parse_header(patch):
    if patch[:4] != b"BPS1":
        raise BPSError("not a BPS patch")
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], "little"):
        raise BPSError("patch checksum mismatch (file damaged)")
    pos = 4
    src_size, pos = decode_number(patch, pos)
    tgt_size, pos = decode_number(patch, pos)
    meta_size, pos = decode_number(patch, pos)
    meta = patch[pos:pos + meta_size]
    pos += meta_size
    return src_size, tgt_size, meta, pos


def apply(source, patch):
    src, patch = bytes(source), bytes(patch)
    src_size, tgt_size, _, pos = parse_header(patch)
    if len(src) != src_size:
        raise BPSError(f"source is {len(src)} bytes, patch expects {src_size}")
    if zlib.crc32(src) != int.from_bytes(patch[-12:-8], "little"):
        raise BPSError("source ROM checksum does not match this patch")
    tgt = bytearray()
    src_rel = tgt_rel = 0
    end = len(patch) - 12
    while pos < end:
        data, pos = decode_number(patch, pos)
        cmd, length = data & 3, (data >> 2) + 1
        if cmd == SOURCE_READ:
            o = len(tgt)
            tgt += src[o:o + length]
        elif cmd == TARGET_READ:
            tgt += patch[pos:pos + length]
            pos += length
        else:
            d, pos = decode_number(patch, pos)
            delta = -(d >> 1) if d & 1 else d >> 1
            if cmd == SOURCE_COPY:
                src_rel += delta
                tgt += src[src_rel:src_rel + length]
                src_rel += length
            else:
                tgt_rel += delta
                for _ in range(length):  # may overlap itself
                    tgt.append(tgt[tgt_rel])
                    tgt_rel += 1
    if len(tgt) != tgt_size:
        raise BPSError(f"output is {len(tgt)} bytes, expected {tgt_size}")
    if zlib.crc32(tgt) != int.from_bytes(patch[-8:-4], "little"):
        raise BPSError("output checksum mismatch")
    return bytes(tgt)


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def main(argv):
    if len(argv) < 2 or argv[1] not in ("create", "apply", "info"):
        print(__doc__)
        return 2
    cmd = argv[1]
    try:
        if cmd == "create" and len(argv) == 5:
            src, tgt = _read(argv[2]), _read(argv[3])
            patch = create(src, tgt, b"Pokemon: Little Trainers")
            if apply(src, patch) != tgt:
                raise BPSError("self-check failed: patch does not reproduce target")
            with open(argv[4], "wb") as f:
                f.write(patch)
            print(f"wrote {argv[4]} ({len(patch):,} bytes), round-trip verified")
        elif cmd == "apply" and len(argv) == 5:
            out = apply(_read(argv[2]), _read(argv[3]))
            with open(argv[4], "wb") as f:
                f.write(out)
            print(f"wrote {argv[4]} ({len(out):,} bytes), checksums OK")
        elif cmd == "info" and len(argv) == 3:
            p = _read(argv[2])
            s, t, m, _ = parse_header(p)
            print(f"source {s:,} bytes crc32 {p[-12:-8][::-1].hex()}\n"
                  f"target {t:,} bytes crc32 {p[-8:-4][::-1].hex()}\nmetadata {m.decode(errors='replace')!r}")
        else:
            print(__doc__)
            return 2
    except (BPSError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
