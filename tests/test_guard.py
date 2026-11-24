"""The forbidden-file guard must block ROMs, saves, patches and credentials, and allow normal files."""
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GBA_HEADER = bytes.fromhex("2e0000ea24ffae51699aa2213d84820a")  # branch + start of the Nintendo logo


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.dir, "scripts"))
        shutil.copy(os.path.join(ROOT, "scripts", "check-forbidden.sh"), os.path.join(self.dir, "scripts"))
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def git(self, *args):
        subprocess.run(["git", "-C", self.dir, *args], check=True, capture_output=True)

    def add(self, name, data):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        self.git("add", "-f", name)

    def check(self, *args):
        return subprocess.run([os.path.join(self.dir, "scripts", "check-forbidden.sh"), *args],
                              capture_output=True, text=True)

    def test_clean_repo_passes(self):
        self.add("README.md", b"hello\n")
        self.add("original-rom/README.md", b"put rom here\n")
        self.assertEqual(self.check("--staged").returncode, 0)

    def test_blocks_rom_by_extension(self):
        self.add("builds/game.gba", b"x")
        self.assertNotEqual(self.check("--staged").returncode, 0)

    def test_blocks_rom_by_content_even_if_renamed(self):
        self.add("docs/notes.dat", GBA_HEADER + b"\0" * 64)
        result = self.check("--staged")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("looks like a GBA ROM", result.stdout)

    def test_blocks_saves_states_patches_and_keys(self):
        for name in ["a.sav", "b.ss1", "c.state", "d.bps", "e.pem", ".env", "bios/gba_bios.bin"]:
            with self.subTest(name=name):
                self.add(name, b"x")
                self.assertNotEqual(self.check("--staged").returncode, 0)
                self.git("rm", "-q", "--cached", name)

    def test_blocks_credentials_in_text(self):
        self.add("config.txt", b"token = ghp_" + b"A" * 36 + b"\n")
        self.assertNotEqual(self.check("--staged").returncode, 0)

    def test_history_scan_finds_deleted_rom(self):
        self.add("oops.txt", GBA_HEADER + b"\0" * 64)
        self.git("commit", "-qm", "oops")
        self.git("rm", "-q", "oops.txt")
        self.git("commit", "-qm", "remove")
        self.assertEqual(self.check().returncode, 0, "tip is clean")
        self.assertNotEqual(self.check("--history").returncode, 0, "but history still holds the ROM")


if __name__ == "__main__":
    unittest.main()
