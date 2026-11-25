"""The Steam Deck installer (`steamdeck/install-little-trainers.py`): install, patch, update.

Everything here runs on made-up "ROMs" a few kilobytes long, in temporary folders, with no
network: the installer's download step is replaced by one that hands over a prepared patch.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import bps                                                                      # noqa: E402

spec = importlib.util.spec_from_file_location("deck", os.path.join(ROOT, "steamdeck", "install-little-trainers.py"))
deck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deck)

SIZE = 8192


def rom(code=b"BPRE", version=1, seed=1):
    """A pretend ROM: repeatable filler with a game code and version where real ROMs keep them."""
    data = bytearray((i * 31 + seed * 7) % 251 for i in range(SIZE))
    data[0xAC:0xB0] = code
    data[0xBC] = version
    return bytes(data)


ORIGINAL = rom()
SHA1 = hashlib.sha1(ORIGINAL).hexdigest()


def game(build):
    """What a build of the hack looks like: the original with some bytes changed and some moved."""
    data = bytearray(ORIGINAL)
    data[100:140] = bytes([build]) * 40
    data[4000:4200] = ORIGINAL[300:500]
    return bytes(data)


def patch_for(build):
    return bps.create(ORIGINAL, game(build))


class Quiet(deck.Ui):
    """Answers yes to everything and remembers what it was told."""

    def __init__(self):
        super().__init__(gui=False, assume_yes=True)
        self.said = []

    def tell(self, text):
        self.said.append(text)

    def confirm(self, text):
        self.said.append(text)
        return True


class Installer(unittest.TestCase):
    def setUp(self):
        self.size = deck.ROM_SIZE
        deck.ROM_SIZE = SIZE
        self.tmp = tempfile.TemporaryDirectory()
        self.roms = os.path.join(self.tmp.name, "roms", "gba")
        os.makedirs(self.roms)
        self.rom_path = os.path.join(self.tmp.name, "my games", "FireRed.gba")
        os.makedirs(os.path.dirname(self.rom_path))
        with open(self.rom_path, "wb") as f:
            f.write(ORIGINAL)
        self.state = os.path.join(self.tmp.name, "config", "install.json")
        self.ui = Quiet()

    def tearDown(self):
        deck.ROM_SIZE = self.size
        self.tmp.cleanup()

    def run_installer(self, build, tag=None, **options):
        args = argparse.Namespace(rom=options.pop("rom", self.rom_path), dest=options.pop("dest", self.roms), patch=None,
                                  check=False, force=False, yes=True, no_gui=True)
        for name, value in options.items():
            setattr(args, name, value)
        self.ui.said.clear()
        return deck.run(args, self.ui, base_sha1=SHA1, state_file=self.state,
                        download=lambda token: (tag or f"v0.0.{build}", patch_for(build)))

    def installed(self):
        with open(os.path.join(self.roms, deck.GAME_FILE), "rb") as f:
            return f.read()

    # --- install -------------------------------------------------------------------------------
    def test_a_first_run_makes_the_game_and_leaves_the_original_alone(self):
        self.assertEqual(self.run_installer(1), 0)
        self.assertEqual(self.installed(), game(1))
        with open(self.rom_path, "rb") as f:
            self.assertEqual(f.read(), ORIGINAL, "the original ROM is only read")
        self.assertEqual(sorted(os.listdir(self.roms)), [deck.GAME_FILE], "nothing else is left in the games folder")
        self.assertIn("v0.0.1 is installed", self.ui.said[-1])

    def test_the_rom_may_be_inside_a_zip(self):
        zipped = os.path.join(self.tmp.name, "FireRed.zip")
        with zipfile.ZipFile(zipped, "w") as archive:
            archive.writestr("Pokemon - FireRed Version (USA, Europe) (Rev 1).gba", ORIGINAL)
        self.assertEqual(self.run_installer(1, rom=zipped), 0)
        self.assertEqual(self.installed(), game(1))

    def test_the_wrong_rom_is_refused_and_named(self):
        for wrong, words in ((rom(version=0), "v1.0"), (rom(code=b"BPGE"), "LeafGreen"), (rom(seed=2), "not an untouched copy"),
                             (b"too short", "right size")):
            path = os.path.join(self.tmp.name, "wrong.gba")
            with open(path, "wb") as f:
                f.write(wrong)
            with self.assertRaises(deck.Stop) as stopped:
                self.run_installer(1, rom=path)
            self.assertIn(words, str(stopped.exception))
            self.assertFalse(os.path.exists(os.path.join(self.roms, deck.GAME_FILE)), "nothing is installed from a wrong ROM")

    def test_the_original_is_never_overwritten(self):
        """Even if the original has the very name the game would get, in the very folder."""
        clash = os.path.join(self.roms, deck.GAME_FILE)
        with open(clash, "wb") as f:
            f.write(ORIGINAL)
        with self.assertRaises(deck.Stop):
            self.run_installer(1, rom=clash)
        with open(clash, "rb") as f:
            self.assertEqual(f.read(), ORIGINAL)

    # --- update --------------------------------------------------------------------------------
    def test_running_again_with_nothing_new_changes_nothing(self):
        self.run_installer(1)
        before = os.stat(os.path.join(self.roms, deck.GAME_FILE)).st_mtime_ns
        self.assertEqual(self.run_installer(1, rom=None, dest=None), 0)
        self.assertIn("already installed", self.ui.said[-1])
        self.assertEqual(os.stat(os.path.join(self.roms, deck.GAME_FILE)).st_mtime_ns, before)

    def test_a_newer_patch_updates_the_game_and_keeps_the_save(self):
        self.run_installer(1)
        save = os.path.join(self.roms, "Pokemon - Little Trainers.sav")
        with open(save, "wb") as f:
            f.write(b"a save file")
        self.assertEqual(self.run_installer(2, rom=None, dest=None), 0, "the ROM and the folder are remembered")
        self.assertEqual(self.installed(), game(2))
        with open(save, "rb") as f:
            self.assertEqual(f.read(), b"a save file")
        self.assertIn("updated from v0.0.1 to v0.0.2", self.ui.said[-1])

    def test_check_only_reports(self):
        self.run_installer(1, check=True)
        self.assertIn("not installed", self.ui.said[-1])
        self.assertFalse(os.path.exists(os.path.join(self.roms, deck.GAME_FILE)))
        self.run_installer(1)
        self.run_installer(1, check=True)
        self.assertIn("is the newest", self.ui.said[-1])
        self.run_installer(2, check=True)
        self.assertIn("An update is available: v0.0.2", self.ui.said[-1])
        self.assertEqual(self.installed(), game(1), "checking does not install")

    def test_a_game_file_that_was_deleted_or_changed_is_made_again(self):
        self.run_installer(1)
        with open(os.path.join(self.roms, deck.GAME_FILE), "wb") as f:
            f.write(b"spoiled")
        self.assertEqual(self.run_installer(1, rom=None, dest=None), 0)
        self.assertEqual(self.installed(), game(1))

    def test_a_patch_file_on_disk_can_be_used_instead_of_downloading(self):
        path = os.path.join(self.tmp.name, "Pokemon-Little-Trainers-v9.9.9.bps")
        with open(path, "wb") as f:
            f.write(patch_for(3))
        args = argparse.Namespace(rom=self.rom_path, dest=self.roms, patch=path, check=False, force=False, yes=True, no_gui=True)

        def no_network(token):
            raise AssertionError("nothing should be downloaded")

        self.assertEqual(deck.run(args, self.ui, base_sha1=SHA1, state_file=self.state, download=no_network), 0)
        self.assertEqual(self.installed(), game(3))
        self.assertIn("v9.9.9", self.ui.said[-1])


class PopUpWindows(unittest.TestCase):
    """On the Deck the questions are asked with zenity. Here a stand-in program takes its place:
    it writes down what it was asked and answers from a list, so the installer's side of the
    conversation is checked. (The real zenity is not run by these tests.)"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "asked.txt")
        self.answers = os.path.join(self.tmp.name, "answers.txt")
        stand_in = os.path.join(self.tmp.name, "zenity")
        with open(stand_in, "w") as f:
            f.write(f"""#!/usr/bin/env python3
import sys
with open({self.log!r}, "a") as log:
    log.write("\\t".join(sys.argv[1:]) + "\\n")
kind = next((a for a in sys.argv[1:] if a in ("--info", "--error", "--question", "--file-selection")), "")
if kind in ("--info", "--error"):
    sys.exit(0)
with open({self.answers!r}) as f:
    lines = f.read().splitlines()
answer, rest = lines[0], lines[1:]
with open({self.answers!r}, "w") as f:
    f.write("\\n".join(rest) + ("\\n" if rest else ""))
if answer == "CANCEL":
    sys.exit(1)
if kind == "--file-selection":
    print(answer)
sys.exit(0)
""")
        os.chmod(stand_in, 0o755)
        self.env = {k: os.environ.get(k) for k in ("PATH", "DISPLAY")}
        os.environ["PATH"] = self.tmp.name + os.pathsep + os.environ["PATH"]
        os.environ["DISPLAY"] = ":0"
        self.size = deck.ROM_SIZE
        deck.ROM_SIZE = SIZE
        self.quiet = contextlib.ExitStack()             # the installer also prints what it says in windows
        self.quiet.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.quiet.enter_context(contextlib.redirect_stderr(io.StringIO()))

    def tearDown(self):
        self.quiet.close()
        deck.ROM_SIZE = self.size
        for key, value in self.env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def answer(self, *lines):
        with open(self.answers, "w") as f:
            f.write("\n".join(lines) + "\n")

    def asked(self):
        with open(self.log) as f:
            return f.read()

    def test_a_first_install_by_pop_up_windows(self):
        """Nothing is known: the ROM is picked, a wrong one first; the folder is picked."""
        wrong = os.path.join(self.tmp.name, "LeafGreen.gba")
        right = os.path.join(self.tmp.name, "FireRed.gba")
        games = os.path.join(self.tmp.name, "games")
        os.makedirs(games)
        for path, data in ((wrong, rom(code=b"BPGE")), (right, ORIGINAL)):
            with open(path, "wb") as f:
                f.write(data)
        self.answer(wrong, "YES", right, games)     # pick ROM; "choose a different file?" yes; pick ROM; pick folder
        args = argparse.Namespace(rom=None, dest=None, patch=None, check=False, force=False, yes=False, no_gui=False)
        ui = deck.Ui(gui=True)
        self.assertTrue(ui.zenity, "set-up: the stand-in zenity is found")
        home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(self.tmp.name, "empty-home")       # nothing to find by itself
        try:
            code = deck.run(args, ui, base_sha1=SHA1, state_file=os.path.join(self.tmp.name, "state.json"),
                            download=lambda token: ("v0.0.7", patch_for(7)))
        finally:
            os.environ["HOME"] = home
        self.assertEqual(code, 0)
        with open(os.path.join(games, deck.GAME_FILE), "rb") as f:
            self.assertEqual(f.read(), game(7))
        asked = self.asked()
        self.assertIn("LeafGreen", asked, "the wrong ROM was named")
        self.assertIn("v0.0.7 is installed", asked)
        self.assertIn("--file-selection\t--directory", asked, "the folder was asked for with a folder picker")

    def test_cancelling_a_window_stops_without_installing(self):
        self.answer("CANCEL")
        args = argparse.Namespace(rom=None, dest=None, patch=None, check=False, force=False, yes=False, no_gui=False)
        home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(self.tmp.name, "empty-home")
        try:
            with self.assertRaises(deck.Stop):
                deck.run(args, deck.Ui(gui=True), base_sha1=SHA1, state_file=os.path.join(self.tmp.name, "state.json"),
                         download=lambda token: ("v0.0.7", patch_for(7)))
        finally:
            os.environ["HOME"] = home


class Patching(unittest.TestCase):
    def test_a_patch_made_by_the_project_applies(self):
        self.assertEqual(deck.apply_bps(ORIGINAL, patch_for(5)), game(5))

    def test_a_damaged_patch_is_refused(self):
        patch = bytearray(patch_for(5))
        patch[20] ^= 0xFF
        with self.assertRaises(deck.Stop):
            deck.apply_bps(ORIGINAL, bytes(patch))
        with self.assertRaises(deck.Stop):
            deck.apply_bps(ORIGINAL, b"not a patch at all")

    def test_a_patch_for_another_rom_is_refused(self):
        with self.assertRaises(deck.Stop):
            deck.apply_bps(rom(seed=9), patch_for(5))


class Releases(unittest.TestCase):
    def asset(self, name):
        return {"name": name, "url": "api/" + name, "browser_download_url": "dl/" + name}

    def test_the_newest_published_release_with_a_patch_is_chosen_test_builds_included(self):
        releases = [
            {"tag_name": "v9-draft", "draft": True, "prerelease": True, "assets": [self.asset("x.bps")]},
            {"tag_name": "v3-notes-only", "draft": False, "prerelease": False, "assets": []},
            {"tag_name": "v2", "draft": False, "prerelease": True, "assets": [self.asset("SHA256SUMS.txt"), self.asset("Pokemon-Little-Trainers-v2.bps")]},
            {"tag_name": "v1", "draft": False, "prerelease": True, "assets": [self.asset("Pokemon-Little-Trainers-v1.bps")]},
        ]
        chosen = deck.newest_release(releases)
        self.assertEqual(chosen["tag"], "v2")
        self.assertEqual(chosen["patch"]["name"], "Pokemon-Little-Trainers-v2.bps")
        self.assertEqual(chosen["sums"]["name"], "SHA256SUMS.txt")
        self.assertIsNone(deck.newest_release([]))


if __name__ == "__main__":
    unittest.main()
