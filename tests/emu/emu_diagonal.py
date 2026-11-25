"""The arrow points diagonally when the way ahead turns a corner and either direction is right.

Jake asked for diagonal directions (2026-11-25). The player can only step up, down, left or
right, so a diagonal arrow is a promise: pressing either of its two directions is a good step.
These tests hold the game to that promise.
"""
import unittest

from .checkpoints import game_at
from . import emu_playtest1

VIRIDIAN_CITY = (3, 1)
DELTA = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}


def walk_to_viridian(g, take_second):
    """Follow the arrow from Route 1 to Viridian City. With `take_second`, whenever the arrow is
    diagonal take its other direction instead of the path's own next step. Returns the steps
    taken, the diagonal arrows seen as (shown, first, second), and any step that hit something."""
    steps, diagonals, bumps = 0, [], []
    for _ in range(3000):
        if g.location() == VIRIDIAN_CITY and g.free_to_move():
            return steps, diagonals, bumps
        if g.in_battle():
            while g.wait_action_menu():
                g.run_away()
            continue
        if not g.free_to_move():
            g.press("A", hold=3, wait=17)
            continue
        g.frames(3)
        first, second, shown = g.nav_arrow(), g.nav_arrow_second(), g.nav_arrow_shown()
        if first is None:
            g.press("A", hold=3, wait=17)
            continue
        if second:
            diagonals.append((shown, first, second))
        direction = second if (second and take_second) else first
        before = g.position()
        if g.step(direction):
            steps += 1
        elif not g.in_battle() and g.free_to_move() and g.position() == before:
            bumps.append((before, shown, direction))
    raise AssertionError(f"did not reach Viridian City; at {g.position()} on {g.location()}")


class DiagonalArrow(unittest.TestCase):
    def test_either_direction_of_a_diagonal_arrow_is_a_good_step(self):
        g = game_at("route1")
        try:
            usual_steps, usual_diagonals, usual_bumps = walk_to_viridian(g, take_second=False)
        finally:
            g.close()
        g = game_at("route1")
        try:
            other_steps, other_diagonals, other_bumps = walk_to_viridian(g, take_second=True)
        finally:
            g.close()
        self.assertGreaterEqual(len(usual_diagonals), 3, "the walk up Route 1 turns corners: diagonal arrows show")
        for shown, first, second in usual_diagonals + other_diagonals:
            self.assertEqual(sorted(shown.split("-")), sorted([first, second]),
                             "the picture points between the path's next step and the other good step")
            self.assertEqual({first in ("UP", "DOWN"), second in ("UP", "DOWN")}, {True, False},
                             f"{shown}: one of its directions is up or down, the other left or right")
        self.assertEqual(usual_bumps, [], "following the path's own step never walks into anything")
        self.assertEqual(other_bumps, [], "taking the other direction of a diagonal arrow never walks into anything")
        self.assertLessEqual(other_steps, usual_steps + 4, "and it is no longer a walk")


class DiagonalArrowPicture(unittest.TestCase):
    arrow_picture = emu_playtest1.ArrowPicture.arrow_picture       # the arrow as the console draws it

    def test_the_diagonal_arrow_is_one_whole_arrow_pointing_into_its_corner(self):
        g = game_at("route1")
        try:
            seen = {}

            def seen_a_diagonal():
                shown = g.nav_arrow_shown() if g.free_to_move() else None
                if shown and "-" in shown and shown not in seen:
                    seen[shown] = self.arrow_picture(g)
                return bool(seen)

            g.follow_arrow(seen_a_diagonal, max_actions=600, what="a diagonal arrow")
            for shown, grid in seen.items():
                # Turn the picture so that it should point up and to the right.
                if "DOWN" in shown:
                    grid = grid[::-1]
                if "LEFT" in shown:
                    grid = [row[::-1] for row in grid]
                picture = "\n".join("".join("#" if c else "." for c in row) for row in grid)
                for y in range(16):
                    for x in range(16):
                        self.assertEqual(grid[y][x], grid[15 - x][15 - y], f"{shown}: the two sides of the arrow match\n{picture}")
                # Slices across the arrow, from the tail (bottom-left) to the point (top-right)
                slices = {k: sum(grid[y][x] for y in range(16) for x in range(16) if x - y == k) for k in range(-15, 16)}
                inked = [k for k in slices if slices[k]]
                widest = max(inked, key=lambda k: slices[k])
                self.assertLessEqual(slices[max(inked)], 2, f"{shown}: it comes to a point at the front\n{picture}")
                self.assertGreater(widest, 0, f"{shown}: the head is in the half nearer the corner it points to\n{picture}")
                self.assertLessEqual(min(inked), -8, f"{shown}: it has a tail\n{picture}")
                for k in inked:
                    if k <= widest - 4:
                        self.assertLessEqual(slices[k] * 2, slices[widest], f"{shown}: the tail is much narrower than the head\n{picture}")
            g.shot("arrow-diagonal")
        finally:
            g.close()


if __name__ == "__main__":
    unittest.main()
