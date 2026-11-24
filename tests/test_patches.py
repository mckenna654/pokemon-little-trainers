"""Checks that patches/, upstream.lock and game/ agree. Work-tree checks are skipped when
scripts/setup.sh has not been run (for example in the lightweight CI job)."""
import os
import subprocess
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GAME = os.path.join(ROOT, "game")
LOCK = dict(line.split("=", 1) for line in Path(ROOT, "upstream.lock").read_text().split("\n")
            if line and not line.startswith("#"))
PATCHES = sorted(p for p in os.listdir(os.path.join(ROOT, "patches")) if p.endswith(".patch"))


def git(*args):
    return subprocess.run(["git", "-C", GAME, *args], check=True, capture_output=True, text=True).stdout


class LockTests(unittest.TestCase):
    def test_pins_are_full_hashes(self):
        for key in ["UPSTREAM_COMMIT", "AGBCC_COMMIT", "BASE_ROM_SHA1"]:
            self.assertRegex(LOCK[key], r"^[0-9a-f]{40}$", key)
        self.assertRegex(LOCK["BASE_ROM_SHA256"], r"^[0-9a-f]{64}$")

    def test_single_supported_revision(self):
        self.assertEqual(LOCK["BUILD_TARGET"], "firered_rev1")


class PatchFileTests(unittest.TestCase):
    def test_patches_are_numbered_and_reasonably_small(self):
        for i, p in enumerate(PATCHES, start=1):
            self.assertTrue(p.startswith(f"{i:04d}-"), f"{p} is out of sequence")
            self.assertLess(os.path.getsize(os.path.join(ROOT, "patches", p)), 4 * 1024 * 1024, p)

    @unittest.skipUnless(PATCHES, "no patches yet")
    def test_config_header_is_introduced(self):
        text = "".join(Path(ROOT, "patches", p).read_text(encoding="utf-8", errors="replace") for p in PATCHES)
        self.assertIn("include/little_trainers.h", text)


@unittest.skipUnless(os.path.isdir(os.path.join(GAME, ".git")), "game/ not set up")
class WorkTreeTests(unittest.TestCase):
    def test_branch_built_on_pinned_upstream(self):
        base = git("merge-base", "little-trainers", LOCK["UPSTREAM_COMMIT"]).strip()
        self.assertEqual(base, LOCK["UPSTREAM_COMMIT"])

    def test_every_commit_is_exported(self):
        count = int(git("rev-list", "--count", f'{LOCK["UPSTREAM_COMMIT"]}..little-trainers').strip())
        self.assertEqual(count, len(PATCHES), "run scripts/export-patches.sh")

    def test_cannot_push_to_pret(self):
        self.assertNotIn("github.com", git("remote", "get-url", "--push", "upstream"))


if __name__ == "__main__":
    unittest.main()
