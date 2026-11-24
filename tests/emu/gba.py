"""Drive the compiled ROM in a real (headless) mGBA core through work/gbarun.

    with GBA(rom, sym) as g:
        g.press("A")
        g.run_until(lambda: g.r8(g.sym("gMain") + ...) == 1, mash="A")

All timing is in frames (60 per second of game time). Runs are deterministic: the same inputs on
the same ROM give the same result, so tests are repeatable.
"""
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GBARUN = os.path.join(ROOT, "work", "gbarun")
KEYS = {"A": 1, "B": 2, "SELECT": 4, "START": 8, "RIGHT": 16, "LEFT": 32, "UP": 64, "DOWN": 128, "R": 256, "L": 512}


class EmulatorError(Exception):
    pass


def load_symbols(path):
    """Parse `arm-none-eabi-nm -n` output into {name: address}."""
    table = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 3:
                table[parts[2]] = int(parts[0], 16)
    return table


class GBA:
    def __init__(self, rom, sym=None, save=None):
        if not os.path.exists(GBARUN):
            raise EmulatorError("work/gbarun is missing: run scripts/build-emu.sh")
        args = [GBARUN, rom] + ([save] if save else [])
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        ready = self.proc.stdout.readline()
        if not ready.startswith("ok ready"):
            raise EmulatorError(f"emulator did not start: {ready!r}")
        self.symbols = load_symbols(sym) if sym else {}
        self.frame = 0

    # --- plumbing -------------------------------------------------------------------------
    def cmd(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()
        reply = self.proc.stdout.readline().strip()
        if not reply.startswith("ok"):
            raise EmulatorError(f"{text!r} -> {reply!r}")
        return reply[3:]

    def close(self):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.write("quit\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
        for stream in (self.proc.stdin, self.proc.stdout):
            try:
                stream.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # --- time and input -------------------------------------------------------------------
    def frames(self, n=1):
        self.frame = int(self.cmd(f"f {n}"))

    def hold(self, *keys):
        self.cmd(f"k {sum(KEYS[k] for k in keys)}")

    def press(self, key, hold=3, wait=12):
        """Tap a button: held for `hold` frames, then released for `wait` frames."""
        self.hold(key)
        self.frames(hold)
        self.hold()
        self.frames(wait)

    def walk(self, direction, tiles=1, run=False):
        """Hold a direction long enough to move `tiles` tiles (16 frames per tile walking)."""
        keys = (direction, "B") if run else (direction,)
        self.hold(*keys)
        self.frames((8 if run else 16) * tiles)
        self.hold()
        self.frames(2)

    def run_until(self, condition, mash=None, max_frames=60 * 60 * 3, step=20, what="condition"):
        """Advance until condition() is true, optionally tapping `mash` (a key or list of keys)."""
        keys = [mash] if isinstance(mash, str) else list(mash or [])
        start, i = self.frame, 0
        while not condition():
            if self.frame - start > max_frames:
                raise EmulatorError(f"timed out after {max_frames} frames waiting for {what}")
            if keys:
                self.press(keys[i % len(keys)], hold=3, wait=max(1, step - 3))
                i += 1
            else:
                self.frames(step)

    # --- memory ---------------------------------------------------------------------------
    def sym(self, name):
        try:
            return self.symbols[name]
        except KeyError:
            raise EmulatorError(f"symbol {name} not found (rebuild so builds/*.sym is current)") from None

    def r8(self, addr):
        return int(self.cmd(f"r8 {addr}"))

    def r16(self, addr):
        return int(self.cmd(f"r16 {addr}"))

    def r32(self, addr):
        return int(self.cmd(f"r32 {addr}"))

    def w8(self, addr, value):
        self.cmd(f"w8 {addr} {value}")

    def w16(self, addr, value):
        self.cmd(f"w16 {addr} {value}")

    def w32(self, addr, value):
        self.cmd(f"w32 {addr} {value}")

    def read(self, addr, length):
        return bytes.fromhex(self.cmd(f"rb {addr} {length}"))

    # --- files ----------------------------------------------------------------------------
    def screenshot(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.cmd(f"shot {os.path.abspath(path)}")

    def save_state(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.cmd(f"ss {os.path.abspath(path)}")

    def load_state(self, path):
        self.cmd(f"ls {os.path.abspath(path)}")

    def reset(self):
        self.cmd("reset")
