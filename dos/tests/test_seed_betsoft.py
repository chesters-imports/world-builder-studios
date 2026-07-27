"""Betsoft office snapshot seed — frozen Roadmaps campus."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dos.cli import ensure_world
from dos.commands import dispatch
from dos.format import plain
from dos.seed import (
    install_snapshot_seed,
    is_snapshot_seed,
    normalize_seed_flavor,
    snapshot_path_for,
)


class BetsoftSnapshotSeedTests(unittest.TestCase):
    def test_aliases_and_snapshot_path(self) -> None:
        for alias in ("betsoft", "bsg", "roadmap", "roadmaps", "castaway"):
            self.assertEqual(normalize_seed_flavor(alias), "betsoft")
            self.assertTrue(is_snapshot_seed(alias))
        path = snapshot_path_for("betsoft")
        assert path is not None
        self.assertTrue(
            path.is_file(),
            msg=f"Missing frozen campus {path} — do not reseed without it",
        )

    def test_install_restores_roadmap_labor(self) -> None:
        tmp = Path(tempfile.mkdtemp()) / "betsoft-test.world.db"
        install_snapshot_seed(tmp, "betsoft")
        self.assertTrue(tmp.is_file())
        w = ensure_world(tmp, reseed=False, seed="betsoft")
        # Castaway title + production date tickets must be present
        names = [
            plain(
                (r[0] or "")
            )
            for r in w.conn.execute(
                """
                SELECT COALESCE(NULLIF(i.name_override, ''), v.name)
                FROM instances i
                JOIN vens v ON v.id = i.ven_id
                """
            )
        ]
        joined = "\n".join(names)
        self.assertIn("Roadmap Location", joined)
        self.assertTrue(
            any("Castaway" in n for n in names),
            msg=joined[:800],
        )
        self.assertTrue(
            any("Production Dates" in n for n in names),
            msg=joined[:800],
        )
        # Ticket count — full map dates
        n_tickets = w.conn.execute(
            """
            SELECT count(*) FROM instances i
            JOIN vens v ON v.id = i.ven_id
            WHERE lower(v.kind) = 'ticket'
            """
        ).fetchone()[0]
        self.assertGreaterEqual(n_tickets, 15)

    def test_reseed_via_ensure_world(self) -> None:
        tmp = Path(tempfile.mkdtemp()) / "betsoft-reseed.world.db"
        w = ensure_world(tmp, reseed=True, seed="betsoft")
        look = plain(dispatch(w, "look").message)
        # Operator starts somewhere in the Betsoft campus
        self.assertTrue(look.strip(), msg="empty look after betsoft reseed")


if __name__ == "__main__":
    unittest.main()
