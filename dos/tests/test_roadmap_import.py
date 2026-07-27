"""Confluence date-list → floor product + Production Dates tickets."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dos.commands import dispatch
from dos.db import connect
from dos.format import plain
from dos.multiline_open import commit_multiline_session, parse_multiline_opener
from dos.roadmap_import import (
    clean_phase_label,
    parse_confluence_date_list,
    parse_product_title,
    parse_roadmap_blob,
    materialize_roadmap_on_floor,
)
from dos.seed import seed_world_office
from dos.world import World

SAMPLE = """
Nov 17, 2025 - Dec 15, 2025: Design Phase & Math Start (4 weeks)

Dec 15, 2025 - Feb 9, 2026: Static Art Phase (7 weeks) + (1 week for Holidays) ← Extra 3 weeks given due to Art team work overload.

Feb 9, 2026 - Mar 9, 2026: FX Phase (4 weeks)

Feb 9, 2026: Math and Specs to Devs (4 weeks before All Assets)

Mar 9, 2026: All Assets to Devs

Jul 14, 2026 - Jul 15, 2026: Active Rollout (Tuesday - Wednesday)

July 16, 2026: Global Release (Thursday)

Note: Exclusivity removed
"""


def _office() -> World:
    tmp = tempfile.NamedTemporaryFile(suffix=".world.db", delete=False)
    tmp.close()
    conn = connect(Path(tmp.name))
    seed_world_office(conn)
    return World(conn)


class ParseRoadmapTests(unittest.TestCase):
    def test_product_title(self) -> None:
        self.assertEqual(
            parse_product_title("27BG-111 - The Castaway"),
            ("The Castaway", "27BG-111"),
        )
        self.assertEqual(
            parse_product_title("The Castaway (27BG-111)"),
            ("The Castaway", "27BG-111"),
        )
        self.assertEqual(parse_product_title("Solo Title"), ("Solo Title", ""))

    def test_clean_label(self) -> None:
        self.assertEqual(
            clean_phase_label("Design Phase & Math Start (4 weeks)"),
            "Design Phase & Math Start",
        )
        self.assertEqual(
            clean_phase_label(
                "Static Art Phase (7 weeks) + (1 week for Holidays) "
                "← Extra 3 weeks given"
            ),
            "Static Art Phase",
        )
        self.assertEqual(
            clean_phase_label("Active Rollout (Tuesday - Wednesday)"),
            "Active Rollout",
        )
        self.assertEqual(
            clean_phase_label("Beta QA (Product + Math QA) (2 weeks)."),
            "Beta QA",
        )
        self.assertEqual(
            clean_phase_label(
                "Request RQA Testing for English version only (Monday)"
            ),
            "Request RQA Testing",
        )
        self.assertEqual(
            clean_phase_label(
                "Product Sheets Distributed to AM Team which requires "
                "Simulation Stats Confirmed by Math Team for All Models"
            ),
            "Product Sheets Distributed to AM Team",
        )
        self.assertEqual(
            clean_phase_label("Audio Team Deadline: (4 weeks before Product QA)"),
            "Audio Team Deadline",
        )

    def test_parse_sample_blob(self) -> None:
        phases, notes = parse_confluence_date_list(SAMPLE)
        self.assertGreaterEqual(len(phases), 7)
        names = [p.name for p in phases]
        self.assertIn("Design Phase & Math Start", names)
        self.assertIn("Global Release", names)
        self.assertIn("Math and Specs to Devs", names)
        design = next(p for p in phases if "Design" in p.name)
        self.assertEqual(design.kind, "range")
        self.assertIn("Nov 17, 2025", design.date_desc)
        self.assertIn("Dec 15, 2025", design.date_desc)
        point = next(p for p in phases if p.name == "All Assets to Devs")
        self.assertEqual(point.kind, "point")
        self.assertIn("Exclusivity", " ".join(notes))


class MaterializeRoadmapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = _office()

    def test_spawns_on_floor_with_tickets(self) -> None:
        msg, meta = materialize_roadmap_on_floor(
            self.world,
            title="27BG-999 - Demo Slot",
            body=SAMPLE,
        )
        text = plain(msg)
        self.assertIn("Roadmap imported", text)
        self.assertIn("Demo Slot", text)
        self.assertGreaterEqual(meta.get("ticket_count", 0), 7)
        product = self.world.get_instance(meta["product_id"])
        assert product is not None
        # on floor of lobby (player start)
        loc = self.world.player_location()
        assert loc is not None
        kids = self.world.contents(loc.id)
        self.assertTrue(any(c.id == product.id for c in kids))
        dates = self.world.get_instance(meta["dates_id"])
        assert dates is not None
        tickets = self.world.contents(dates.id)
        self.assertGreaterEqual(len(tickets), 7)
        tnames = [t.name for t in tickets]
        self.assertTrue(any("Design Phase" in (n or "") for n in tnames))

    def test_multiline_opener_and_commit(self) -> None:
        sess = parse_multiline_opener("import roadmap <<studio")
        assert sess is not None
        self.assertEqual(sess.kind, "roadmap_import")
        r = commit_multiline_session(
            self.world,
            sess,
            SAMPLE,
            page_title="99ZZ-001 - Paste Title",
        )
        self.assertTrue(r.ok, msg=r.message)
        self.assertIn("Roadmap imported", plain(r.message or ""))

    def test_import_from_folio_leaf(self) -> None:
        dispatch(self.world, "create book Date Dump | holds a paste.")
        dispatch(self.world, "spawn date-dump")
        book = self.world.resolve_here_named("date-dump")
        assert book is not None
        self.world.add_book_page(
            book.id,
            "88AA-002 - From Folio",
            SAMPLE,
        )
        r = dispatch(self.world, "import roadmap from date-dump 1")
        self.assertTrue(r.ok, msg=r.message)
        self.assertIn("From Folio", plain(r.message))


if __name__ == "__main__":
    unittest.main()
