"""Cached save states for emulator tests, keyed by the ROM's hash (a save state is only valid for
the exact build that made it). Stored in work/emu-cache/, never committed."""
import hashlib
import os

from .firered import ROM, SYM, FireRed
from .gba import ROOT
from . import story


def _cache_dir(rom):
    with open(rom, "rb") as f:
        digest = hashlib.sha1(f.read()).hexdigest()[:16]
    path = os.path.join(ROOT, "work", "emu-cache", digest)
    os.makedirs(path, exist_ok=True)
    return path


def game_at(name, rom=ROM, sym=SYM, starter="charmander"):
    """Return a running game at a named checkpoint, replaying the story only on a cache miss.

    Checkpoints: "starter"  - in Oak's lab holding the chosen starter, before the rival battle
                 "route1"   - standing on Route 1 after winning the rival battle
    """
    g = FireRed(rom, sym)
    state = os.path.join(_cache_dir(rom), f"{name}-{starter}.ss")
    if os.path.exists(state):
        g.frames(5)
        g.load_state(state)
        g.frames(2)
        return g
    if name == "starter":
        story.new_game_to_starter(g, starter)
    elif name == "route1":
        story.new_game_to_starter(g, starter)
        story.win_rival_battle(g)
        story.to_route1(g)
    else:
        raise ValueError(name)
    g.save_state(state)
    return g
