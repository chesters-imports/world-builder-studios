"""Clickable look names / bin headers (@click → look at)."""

from __future__ import annotations

import unittest

from dos import format as fmt
from dos.commands import _bin_bucket_header, dispatch
from dos.db import connect
from dos.seed import seed_world
from dos.world import World
from pathlib import Path
import tempfile


class ClickLookMarkupTests(unittest.TestCase):
    def test_click_look_wraps_ref(self) -> None:
        s = fmt.click_look("q3-abcd", "[bold]Q3[/bold]")
        self.assertIn("@click=app.look_at('q3-abcd')", s)
        self.assertIn("[bold]Q3[/bold]", s)

    def test_click_look_skips_empty(self) -> None:
        self.assertEqual(fmt.click_look("", "x"), "x")
        self.assertEqual(fmt.click_look("—", "x"), "x")

    def test_look_bin_header_and_row_are_clickable(self) -> None:
        p = Path(tempfile.mkdtemp()) / "click.world.db"
        conn = connect(p)
        seed_world(conn, flavor="office")
        w = World(conn)
        self.assertTrue(dispatch(w, "dig bin Q3 | Quarter shelf").ok)
        self.assertTrue(dispatch(w, "dig thing Title A | Game card").ok)
        self.assertTrue(dispatch(w, "put Title A in Q3").ok)
        r = dispatch(w, "look")
        msg = r.message or ""
        self.assertIn("@click=app.look_at", msg)
        # Bin section title + room items (handbook, title when loose, …)
        self.assertGreaterEqual(msg.count("@click=app.look_at"), 2)
        plain = fmt.plain(msg)
        self.assertIn("Q3", plain)
        # Inside the bin, child still clickable
        r2 = dispatch(w, "look at Q3")
        msg2 = r2.message or ""
        self.assertIn("Title A", fmt.plain(msg2))
        self.assertIn("@click=app.look_at", msg2)


if __name__ == "__main__":
    unittest.main()
