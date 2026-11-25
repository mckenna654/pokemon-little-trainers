#!/usr/bin/env python3
"""Pokémon: Little Trainers - install, patch and update on a Steam Deck (or any Linux PC).

Run it again at any time to update: it fetches the newest patch and rebuilds the game from your
own FireRed ROM. Your original ROM is only ever read, and your save file is left alone.

    Easiest: in Desktop Mode, open this file from the file manager and choose "Execute".
    Or in Konsole:   python3 install-little-trainers.py

What it does:
  1. finds your Pokémon FireRed (USA, Europe) v1.1 ROM, or asks you to pick it
  2. downloads the newest Little Trainers patch from GitHub and checks it arrived intact
  3. makes the patched game next to your other GBA games (EmuDeck and RetroDECK folders are found
     by themselves), as "Pokemon - Little Trainers.gba"
  4. remembers what it did, so running it again only does something when there is a newer patch

Options (all optional; with none it asks, using pop-up windows when it can):
  --rom FILE      your FireRed v1.1 ROM (.gba, or a .zip with the .gba inside)
  --dest FOLDER   where the patched game goes
  --patch FILE    use a patch file you already downloaded instead of fetching the newest
  --check         only say whether an update is available
  --force         rebuild even if the newest patch is already installed
  --yes           do not ask for confirmation
  --no-gui        ask in the terminal instead of with pop-up windows

It needs nothing but Python 3, which SteamOS already has. No administrator password, no changes
outside the folder you choose and ~/.config/little-trainers/. Nothing is uploaded anywhere.
If the project's repository is private, set GITHUB_TOKEN to a token that can read it, or download
the .bps patch yourself and pass it with --patch (or pick it when asked).
"""
import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
import zlib

REPO = "mckenna654/pokemon-little-trainers"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
GAME_FILE = "Pokemon - Little Trainers.gba"
ROM_SIZE = 16 * 1024 * 1024
BASE_SHA1 = "dd5945db9b930750cb39d00c84da8571feebf417"      # FireRed (USA, Europe) v1.1 / Rev 1
GAME_CODES = {          # the four letters every GBA game carries at byte 0xAC of its ROM
    "BPRE": "Pokémon FireRed (USA, Europe)", "BPGE": "Pokémon LeafGreen (USA, Europe)",
    "BPRJ": "Pokémon FireRed (Japan)", "BPRD": "Pokémon FireRed (Germany)", "BPRF": "Pokémon FireRed (France)",
    "BPRI": "Pokémon FireRed (Italy)", "BPRS": "Pokémon FireRed (Spain)",
    "BPEE": "Pokémon Emerald", "AXVE": "Pokémon Ruby", "AXPE": "Pokémon Sapphire",
}
TITLE = "Pokémon: Little Trainers"


class Stop(Exception):
    """Something the player needs to be told; ends the run without a stack trace."""


class NeedsSignIn(Stop):
    """GitHub would not show the releases without a sign-in (the repository is private)."""


# --- BPS patches (the format the project publishes) ------------------------------------------------
def _number(patch, pos):
    value, shift = 0, 1
    while True:
        byte = patch[pos]
        pos += 1
        value += (byte & 0x7F) * shift
        if byte & 0x80:
            return value, pos
        shift <<= 7
        value += shift


def apply_bps(source, patch):
    """The patched file. The patch carries checksums of the ROM it is for, of itself and of the
    result, and all three are checked, so a wrong ROM or a damaged download cannot slip through."""
    if patch[:4] != b"BPS1" or len(patch) < 16:
        raise Stop("That is not a BPS patch file.")
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], "little"):
        raise Stop("The patch file is damaged (it may not have downloaded completely). Try again.")
    pos = 4
    source_size, pos = _number(patch, pos)
    target_size, pos = _number(patch, pos)
    metadata_size, pos = _number(patch, pos)
    pos += metadata_size
    if len(source) != source_size or zlib.crc32(source) != int.from_bytes(patch[-12:-8], "little"):
        raise Stop("This patch is for a different ROM than the one chosen.")
    target = bytearray()
    source_at = target_at = 0
    end = len(patch) - 12
    while pos < end:
        data, pos = _number(patch, pos)
        command, length = data & 3, (data >> 2) + 1
        if command == 0:                                    # the same bytes as the original, in place
            here = len(target)
            target += source[here:here + length]
        elif command == 1:                                  # new bytes, carried in the patch
            target += patch[pos:pos + length]
            pos += length
        else:
            offset, pos = _number(patch, pos)
            offset = -(offset >> 1) if offset & 1 else offset >> 1
            if command == 2:                                # bytes from elsewhere in the original
                source_at += offset
                target += source[source_at:source_at + length]
                source_at += length
            else:                                           # bytes already written (may overlap itself)
                target_at += offset
                for _ in range(length):
                    target.append(target[target_at])
                    target_at += 1
    if len(target) != target_size or zlib.crc32(target) != int.from_bytes(patch[-8:-4], "little"):
        raise Stop("Patching went wrong: the result does not match what the patch expects. Nothing was installed.")
    return bytes(target)


# --- asking and telling ----------------------------------------------------------------------------
class Ui:
    """Pop-up windows through zenity (SteamOS has it), or plain questions in the terminal."""

    def __init__(self, gui=True, assume_yes=False):
        self.zenity = shutil.which("zenity") if gui and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) else None
        self.assume_yes = assume_yes

    def _zenity(self, *args):
        return subprocess.run([self.zenity, f"--title={TITLE}", *args], capture_output=True, text=True)

    def tell(self, text):
        print(text + "\n")
        if self.zenity and not self.assume_yes:
            self._zenity("--info", "--width=520", f"--text={text}")

    def fail(self, text):
        print("Stopped: " + text + "\n", file=sys.stderr)
        if self.zenity:
            self._zenity("--error", "--width=520", f"--text={text}")

    def confirm(self, text):
        if self.assume_yes:
            print(text + " yes\n")
            return True
        if self.zenity:
            return self._zenity("--question", "--width=520", f"--text={text}").returncode == 0
        return self._typed(text + " [y/n] ").lower().startswith("y")

    def pick_file(self, title, patterns, start=None):
        if self.assume_yes:
            return None
        if self.zenity:
            args = ["--file-selection", f"--title={title}", f"--file-filter={title} | " + " ".join(patterns), "--file-filter=All files | *"]
            if start:
                args.append(f"--filename={start.rstrip('/')}/")
            done = self._zenity(*args)
            return done.stdout.strip() or None if done.returncode == 0 else None
        return os.path.expanduser(self._typed(f"{title}\nType the path (or leave empty to stop): ")) or None

    def pick_folder(self, title, start=None):
        if self.assume_yes:
            return None
        if self.zenity:
            args = ["--file-selection", "--directory", f"--title={title}"]
            if start:
                args.append(f"--filename={start.rstrip('/')}/")
            done = self._zenity(*args)
            return done.stdout.strip() or None if done.returncode == 0 else None
        return os.path.expanduser(self._typed(f"{title}\nType the folder (or leave empty to stop): ")) or None

    @staticmethod
    def _typed(prompt):
        try:
            return input(prompt).strip()
        except EOFError:
            return ""


# --- the original ROM ------------------------------------------------------------------------------
def read_rom(path):
    """The bytes of a .gba file, or of the one ROM-sized file inside a .zip; None if it is neither."""
    try:
        if path.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as archive:
                inside = [i for i in archive.infolist() if i.file_size == ROM_SIZE]
                return archive.read(inside[0]) if len(inside) == 1 else None
        if os.path.getsize(path) != ROM_SIZE:
            return None
        with open(path, "rb") as f:
            return f.read()
    except (OSError, zipfile.BadZipFile):
        return None


def judge_rom(path, base_sha1=BASE_SHA1):
    """(bytes, None) for the right ROM, or (None, why not)."""
    data = read_rom(path)
    if data is None:
        return None, f"{os.path.basename(path)} is not a Game Boy Advance ROM of the right size (16 MB)."
    if hashlib.sha1(data).hexdigest() == base_sha1:
        return data, None
    # Say what it is instead, from the name and version number the ROM itself carries.
    name = os.path.basename(path)
    code = data[0xAC:0xB0].decode("ascii", "replace")
    version = data[0xBC]
    if code == "BPRE" and version == 0:
        return None, f"{name} is Pokémon FireRed (USA, Europe) v1.0. Little Trainers needs v1.1 (also called Rev 1)."
    if code == "BPRE":
        return None, (f"{name} says it is Pokémon FireRed (USA, Europe) v1.{version}, but it is not an untouched copy: "
                      "it may already be patched, trimmed or damaged. An unmodified v1.1 is needed.")
    if code in GAME_CODES:
        return None, f"{name} is {GAME_CODES[code]}. Little Trainers is made from Pokémon FireRed (USA, Europe) v1.1."
    return None, f"{name} is not Pokémon FireRed (USA, Europe) v1.1."


def rom_folders():
    """Folders where GBA games usually live on a Deck, the likeliest first. Existing ones only."""
    home = os.path.expanduser("~")
    patterns = [f"{home}/Emulation/roms/gba", "/run/media/*/Emulation/roms/gba", "/run/media/*/*/Emulation/roms/gba",
                f"{home}/retrodeck/roms/gba", "/run/media/*/retrodeck/roms/gba", "/run/media/*/*/retrodeck/roms/gba",
                f"{home}/ROMs/gba", f"{home}/roms/gba"]
    found = []
    for pattern in patterns:
        for folder in sorted(glob.glob(pattern)):
            if os.path.isdir(folder) and folder not in found:
                found.append(folder)
    return found


def find_rom(extra_folders=(), base_sha1=BASE_SHA1):
    """Look through the usual folders (two levels deep) for the right ROM. Only files of exactly
    the right size are read, so this is quick."""
    home = os.path.expanduser("~")
    for folder in [*extra_folders, *rom_folders(), f"{home}/Downloads", f"{home}/Documents", f"{home}/Desktop"]:
        if not os.path.isdir(folder):
            continue
        for root, dirs, files in os.walk(folder):
            if root[len(folder):].count(os.sep) >= 2:
                dirs[:] = []
            for name in sorted(files):
                path = os.path.join(root, name)
                if name == GAME_FILE or not name.lower().endswith((".gba", ".zip")):
                    continue
                try:
                    size = os.path.getsize(path)
                except OSError:
                    continue
                if (name.lower().endswith(".gba") and size == ROM_SIZE) or (name.lower().endswith(".zip") and size < 2 * ROM_SIZE):
                    if judge_rom(path, base_sha1)[0] is not None:
                        return path
    return None


# --- the newest patch ------------------------------------------------------------------------------
class _DropTokenOnRedirect(urllib.request.HTTPRedirectHandler):
    """GitHub hands downloads over to a storage host; the token must not travel there."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.remove_header("Authorization")
        return new


def fetch(url, accept="application/vnd.github+json", token=None):
    request = urllib.request.Request(url, headers={"User-Agent": "little-trainers-installer", "Accept": accept})
    if token and url.startswith("https://api.github.com/"):
        request.add_header("Authorization", "Bearer " + token)
    with urllib.request.build_opener(_DropTokenOnRedirect).open(request, timeout=60) as response:
        return response.read()


def _reason(error):
    reason = getattr(error, "reason", error)
    if "CERTIFICATE_VERIFY_FAILED" in str(reason):
        return "this computer's Python could not check GitHub's security certificate"
    return str(reason)


def newest_release(releases):
    """From GitHub's list of releases (newest first): the first that is published and has a patch.
    Test builds count: so far every build is one. Returns {tag, patch, sums} or None."""
    for release in releases:
        if release.get("draft"):
            continue
        assets = {a["name"]: a for a in release.get("assets", [])}
        patches = [a for name, a in assets.items() if name.lower().endswith(".bps")]
        if patches:
            return {"tag": release["tag_name"], "patch": patches[0], "sums": assets.get("SHA256SUMS.txt")}
    return None


def download_newest(token=None):
    """(tag, patch bytes). Checks the download against the release's list of checksums."""
    try:
        releases = json.loads(fetch(f"https://api.github.com/repos/{REPO}/releases?per_page=20", token=token))
    except urllib.error.HTTPError as error:
        if error.code in (401, 403, 404):
            raise NeedsSignIn("GitHub asked for a sign-in.") from None
        raise Stop(f"GitHub answered with an error ({error.code}). Try again later.") from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise Stop(f"Could not reach GitHub. Check the internet connection and try again.\n\n(What went wrong: {_reason(error)})") from None
    release = newest_release(releases)
    if release is None:
        raise Stop(f"No patch has been published yet. See {RELEASES_PAGE}")

    def asset(a):
        if token:
            return fetch(a["url"], accept="application/octet-stream", token=token)
        return fetch(a["browser_download_url"], accept="*/*")

    try:
        patch = asset(release["patch"])
        sums = asset(release["sums"]).decode() if release["sums"] else ""
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise Stop(f"The download did not finish. Check the internet connection and try again.\n\n(What went wrong: {_reason(error)})") from None
    expected = {line.split()[-1].lstrip("*"): line.split()[0] for line in sums.splitlines() if len(line.split()) >= 2}
    name = release["patch"]["name"]
    if name in expected and hashlib.sha256(patch).hexdigest() != expected[name]:
        raise Stop("The downloaded patch does not match its published checksum. Try again; if it keeps happening, do not use it.")
    return release["tag"], patch


# --- what was done last time -----------------------------------------------------------------------
def state_path():
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "little-trainers", "install.json")


def load_state(path=None):
    try:
        with open(path or state_path()) as f:
            state = json.load(f)
        return state if isinstance(state, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(state, path=None):
    path = path or state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def installed_copy_is_intact(state):
    """True if the game file is still where it was put and still what was put there."""
    try:
        with open(os.path.join(state["dest"], GAME_FILE), "rb") as f:
            return hashlib.sha1(f.read()).hexdigest() == state["game_sha1"]
    except (OSError, KeyError):
        return False


# --- the whole job ---------------------------------------------------------------------------------
def write_game(folder, data, rom_path):
    """Put the game in the folder without ever leaving a half-written file, and never on top of
    the original ROM."""
    target = os.path.join(folder, GAME_FILE)
    if os.path.exists(rom_path) and os.path.exists(target) and os.path.samefile(rom_path, target):
        raise Stop("The original ROM has the name the patched game would get. Rename the original and run this again.")
    os.makedirs(folder, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".little-trainers-", dir=folder)
    try:
        with os.fdopen(handle, "wb") as f:
            f.write(data)
        os.replace(temporary, target)
    except BaseException:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    return target


def run(args, ui, base_sha1=BASE_SHA1, state_file=None, download=download_newest):
    state = load_state(state_file)
    have = state.get("version") if installed_copy_is_intact(state) else None

    # 1. Which patch?
    if args.patch:
        with open(args.patch, "rb") as f:
            patch = f.read()
        tag = os.path.splitext(os.path.basename(args.patch))[0].replace("Pokemon-Little-Trainers-", "")
    else:
        try:
            tag, patch = download(os.environ.get("GITHUB_TOKEN"))
        except NeedsSignIn:
            ui.tell("The newest patch could not be downloaded automatically: the project's page is private "
                    "or asked for a sign-in.\n\n"
                    f"Download the file ending in .bps from\n{RELEASES_PAGE}\nin a web browser, then choose it in the next window.")
            chosen = ui.pick_file("Little Trainers patch (.bps)", ["*.bps"], os.path.expanduser("~/Downloads"))
            if not chosen:
                raise Stop("No patch file was chosen.")
            with open(chosen, "rb") as f:
                patch = f.read()
            tag = os.path.splitext(os.path.basename(chosen))[0].replace("Pokemon-Little-Trainers-", "")
    patch_id = hashlib.sha256(patch).hexdigest()

    if args.check:
        if have is None:
            ui.tell(f"Little Trainers is not installed yet. The newest patch is {tag}.")
        elif state.get("patch_sha256") == patch_id:
            ui.tell(f"Little Trainers {have} is installed and is the newest.")
        else:
            ui.tell(f"An update is available: {tag} (installed: {have}).")
        return 0
    if have is not None and state.get("patch_sha256") == patch_id and not args.force:
        ui.tell(f"Little Trainers {have} is already installed and is the newest. Nothing to do.\n\n{os.path.join(state['dest'], GAME_FILE)}")
        return 0

    # 2. The original ROM
    rom_path = args.rom or state.get("rom")
    rom, why = judge_rom(rom_path, base_sha1) if rom_path and os.path.exists(rom_path) else (None, None)
    if rom is None and args.rom:
        raise Stop(why or f"{args.rom} was not found.")
    if rom is None:
        rom_path = find_rom(base_sha1=base_sha1)
        if rom_path:
            rom = judge_rom(rom_path, base_sha1)[0]
    while rom is None:
        ui.tell("To make the game you need your own Pokémon FireRed ROM: the (USA, Europe) v1.1 version, "
                "a .gba file (it may be inside a .zip).\n\nChoose it in the next window. It will only be read, never changed.")
        folders = rom_folders()
        rom_path = ui.pick_file("Pokémon FireRed v1.1 ROM", ["*.gba", "*.GBA", "*.zip"], folders[0] if folders else os.path.expanduser("~"))
        if not rom_path:
            raise Stop("No ROM was chosen.")
        rom, why = judge_rom(rom_path, base_sha1)
        if rom is None and not ui.confirm((why or "That file cannot be used.") + "\n\nChoose a different file?"):
            raise Stop("The right ROM is needed to continue.")

    # 3. Where the game goes
    dest = args.dest or (state.get("dest") if state.get("dest") and os.path.isdir(state["dest"]) else None)
    if not dest:
        folders = rom_folders()
        dest = folders[0] if folders else None
        if dest is None or not ui.confirm(f"Put the game with your other GBA games?\n\n{dest}"):
            dest = ui.pick_folder("Folder for the patched game", dest or os.path.dirname(os.path.abspath(rom_path)))
            if not dest:
                raise Stop("No folder was chosen.")

    # 4. Patch and install
    if have is not None and not ui.confirm(f"Update Little Trainers from {have} to {tag}?\n\nYour save file is kept."):
        raise Stop("Left as it was.")
    game = apply_bps(rom, patch)
    target = write_game(dest, game, rom_path)
    save_state({"version": tag, "patch_sha256": patch_id, "rom": os.path.abspath(rom_path), "dest": os.path.abspath(dest),
                "game_sha1": hashlib.sha1(game).hexdigest()}, state_file)
    if have is None:
        ui.tell(f"Little Trainers {tag} is installed:\n{target}\n\n"
                "Open it from your GBA emulator like any other game. To see it in Gaming Mode, add it to Steam the way "
                "you add your other emulated games (with EmuDeck, that is Steam ROM Manager).\n\n"
                "Start a new game: saves from the original FireRed do not work with it.\n"
                "Run this installer again whenever you want to check for an update.")
    else:
        ui.tell(f"Little Trainers was updated from {have} to {tag}:\n{target}\n\n"
                "Your save file was not touched and should carry on. These are test builds, so if anything "
                "looks wrong after an update, start a new game.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install, patch and update Pokémon: Little Trainers.",
                                     epilog="With no options it finds things by itself and asks when it cannot.")
    parser.add_argument("--rom", help="your FireRed (USA, Europe) v1.1 ROM: a .gba, or a .zip with it inside")
    parser.add_argument("--dest", help="folder for the patched game")
    parser.add_argument("--patch", help="a .bps patch already downloaded (otherwise the newest is fetched)")
    parser.add_argument("--check", action="store_true", help="only say whether an update is available")
    parser.add_argument("--force", action="store_true", help="rebuild even if the newest patch is installed")
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    parser.add_argument("--no-gui", action="store_true", help="ask in the terminal, not with pop-up windows")
    args = parser.parse_args(argv)
    ui = Ui(gui=not args.no_gui, assume_yes=args.yes)
    try:
        return run(args, ui)
    except Stop as stop:
        ui.fail(str(stop))
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
