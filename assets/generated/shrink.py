"""Shrink a large illustration to a few game pixels by vote, with no image library.

A photo-style resize blends neighbouring colours (a dark outline and a green fill become grey)
and a nearest-pixel resize keeps one source pixel in several hundred, so thin gaps between
letters come and go. Here every source pixel is first snapped to the nearest colour the game
palette has, and each game pixel then takes the colour most of its source pixels voted for.
`weights` lets a colour count for more than its area (the plaque colour between fat letters, so
the letters stay apart).
"""
import struct
import zlib


def colour_distance(a, b):
    """How different two colours look. Brightness alone is not enough: by plain RGB distance a
    mid green is "nearer" to grey than to the palette's own greens, which turned a green bag
    grey. So the two colour-difference channels count three times as much as brightness."""
    def split(c):
        y = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
        return y, c[2] - y, c[0] - y
    (y1, u1, v1), (y2, u2, v2) = split(a), split(b)
    return (y1 - y2) ** 2 + 3 * ((u1 - u2) ** 2 + (v1 - v2) ** 2)


def read_rgba(path):
    """(width, height, rows of bytes) of an 8-bit RGBA PNG; each row is width*4 bytes."""
    with open(path, "rb") as f:
        data = f.read()
    pos, idat = 8, []
    while pos < len(data):
        length, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            width, height, depth, colour_type = struct.unpack(">IIBB", body[:10])
            if (depth, colour_type) != (8, 6):
                raise ValueError(f"{path}: not an 8-bit RGBA picture")
        elif tag == b"IDAT":
            idat.append(body)
    raw, stride = zlib.decompress(b"".join(idat)), width * 4
    rows, prev = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        if kind == 1:
            for i in range(4, stride):
                line[i] = (line[i] + line[i - 4]) & 255
        elif kind == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif kind == 3:
            for i in range(stride):
                line[i] = (line[i] + ((line[i - 4] if i >= 4 else 0) + prev[i]) // 2) & 255
        elif kind == 4:
            for i in range(stride):
                a = line[i - 4] if i >= 4 else 0
                b = prev[i]
                c = prev[i - 4] if i >= 4 else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return width, height, rows


def solid_bounds(width, height, rows, solid=192):
    """The box around the solid ink (faint generated halos are left outside it)."""
    xs, ys = [], []
    for y, row in enumerate(rows):
        alpha = row[3::4]
        if max(alpha) >= solid:
            ys.append(y)
            hits = [x for x in range(width) if alpha[x] >= solid]
            xs += [hits[0], hits[-1]]
    if not ys:
        raise ValueError("no solid artwork")
    return min(xs), ys[0], max(xs) + 1, ys[-1] + 1


def shrink(path, size, palette, allowed, box=None, weights=None, solid=160, cover=0.5):
    """Rows of palette numbers, `size` = (width, height) game pixels. The illustration is cropped
    to its solid ink and fitted, centred, into `box` (default: all of `size`) at the top-left.
    A game pixel is see-through (0) unless at least `cover` of it is ink."""
    width, height, rows = read_rgba(path)
    left, top, right, bottom = solid_bounds(width, height, rows)
    box = box or size
    scale = min(box[0] / (right - left), box[1] / (bottom - top))
    out_w, out_h = max(1, round((right - left) * scale)), max(1, round((bottom - top) * scale))
    off_x, off_y = (box[0] - out_w) // 2, (box[1] - out_h) // 2
    weights = weights or {}
    nearest = {}
    out = [[0] * size[0] for _ in range(size[1])]
    for ty in range(out_h):
        y0, y1 = top + int(ty / scale), min(bottom, top + max(int((ty + 1) / scale), int(ty / scale) + 1))
        for tx in range(out_w):
            x0, x1 = left + int(tx / scale), min(right, left + max(int((tx + 1) / scale), int(tx / scale) + 1))
            votes, clear, total = {}, 0, 0
            for y in range(y0, y1):
                row = rows[y]
                for x in range(x0, x1):
                    r, g, b, a = row[x * 4:x * 4 + 4]
                    total += 1
                    if a < solid:
                        clear += 1
                        continue
                    key = (r >> 3, g >> 3, b >> 3)
                    index = nearest.get(key)
                    if index is None:
                        index = nearest[key] = min(allowed, key=lambda i: colour_distance((r, g, b), palette[i]))
                    votes[index] = votes.get(index, 0) + 1
            if total - clear >= cover * total and votes:
                out[off_y + ty][off_x + tx] = max(votes, key=lambda i: votes[i] * weights.get(i, 1))
    return out
