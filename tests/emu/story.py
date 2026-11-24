"""Scripted story progress, built from real button presses. Each function leaves the player
standing in the overworld with control, so they can be chained:

    g = FireRed(); story.new_game_to_starter(g, "charmander"); story.win_rival_battle(g)
"""
from .firered import OAKS_LAB, PALLET_TOWN, ROUTE1, EmulatorError

VAR_OAKS_LAB_SCENE = 0x4055
STARTER_BALL_TILE = {"bulbasaur": (8, 5), "squirtle": (9, 5), "charmander": (10, 5)}  # stand below the ball
STARTER_SPECIES = {"bulbasaur": 1, "charmander": 4, "squirtle": 7}


def leave_house(g):
    g.start_new_game()
    g.take_warp(10, 2)          # bedroom stairs
    g.take_warp(4, 8)           # front door mat
    if g.location() != PALLET_TOWN:
        raise EmulatorError(f"expected Pallet Town, got {g.location()}")


def meet_oak(g):
    """Walk towards Route 1; Oak stops the player and leads them to the lab."""
    g.go_to(12, 1)
    g.advance_text(lambda: g.location() == OAKS_LAB and g.free_to_move(), what="control in Oak's lab")


def choose_starter(g, starter="charmander"):
    g.go_to(*STARTER_BALL_TILE[starter])
    g.hold("UP"); g.frames(8); g.hold(); g.frames(10)      # face the ball
    g.advance_text(lambda: g.party_count() == 1, what="receiving the starter")
    g.advance_text(g.free_to_move, what="control after choosing")
    g.settle()                                              # the autosave that follows a completed goal
    mon = g.party()[0]
    if mon.species != STARTER_SPECIES[starter]:
        raise EmulatorError(f"expected {starter}, got species {mon.species}")
    return mon


def start_rival_battle(g):
    g.go_to(6, 8)               # walking towards the exit triggers the rival
    g.advance_text(g.in_battle, what="rival battle to start")


def finish_battle(g, max_presses=2500):
    """Mash A (first menu option, first move) until the battle is over and control returns."""
    g.advance_text(lambda: not g.in_battle() and g.free_to_move(), max_presses=max_presses, what="battle to end")
    return g.battle_outcome()


def new_game_to_starter(g, starter="charmander"):
    leave_house(g)
    meet_oak(g)
    return choose_starter(g, starter)


def win_rival_battle(g):
    start_rival_battle(g)
    return finish_battle(g)


def to_route1(g):
    """From Oak's lab (after the rival battle) to Route 1. On the way out of Pallet Town an NPC
    may stop the player to show them a sign; that conversation is tapped through."""
    g.take_warp(6, 12)
    for _ in range(6):
        if g.location() == ROUTE1:
            break
        if not g.free_to_move():
            g.advance_text(g.free_to_move, what="control in Pallet Town")
        try:
            g.go_to(12, 0)
        except EmulatorError:
            g.go_to(13, 0)
        if g.free_to_move() and g.location() == PALLET_TOWN and g.position()[1] == 0:
            g.step("UP")
    g.frames(30)
    if g.location() != ROUTE1:
        raise EmulatorError(f"expected Route 1, got {g.location()} at {g.position()}")


def find_wild_battle(g, max_trips=40):
    """Walk around Route 1's first grass patches until a wild Pokémon appears."""
    spots = [(13, 33), (4, 33), (13, 35), (4, 35), (17, 28), (4, 28)]
    for i in range(max_trips):
        if g.in_battle() or not g.free_to_move():
            break
        g.go_to(*spots[i % len(spots)])
    g.run_until(g.in_battle, max_frames=900, what="wild battle to start")
