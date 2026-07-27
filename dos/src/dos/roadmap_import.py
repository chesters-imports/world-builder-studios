"""Port Confluence-style plain date lists into DOS roadmap furniture.

Source format (product ops paste)::

    Nov 17, 2025 - Dec 15, 2025: Design Phase & Math Start (4 weeks)
    Mar 9, 2026: All Assets to Devs
    Note: Exclusivity removed

Studio / folio leaf:
  **Title** → product code + name  (e.g. ``27BG-111 - The Castaway``)
  **Body**  → the date list above

Spawns on the floor (player place): product bin → Production Dates → tickets.
User moves the product into quarter/month bins themselves.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .world import World

# Month names as ops types them (Jul / July, Sept, …)
_MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)"
)
_DATE = rf"{_MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}"
_DATE_RE = re.compile(rf"^{_DATE}$", re.IGNORECASE)
_RANGE_RE = re.compile(
    rf"^({_DATE})\s*[-–—]\s*({_DATE})$",
    re.IGNORECASE,
)

# Title: "27BG-111 - The Castaway" or "27BG-111 — The Castaway"
_TITLE_CODE_NAME = re.compile(
    r"^(?P<code>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\s*[-–—:|]\s*(?P<name>.+)$"
)
# "The Castaway (27BG-111)"
_TITLE_NAME_CODE = re.compile(
    r"^(?P<name>.+?)\s*\((?P<code>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\)\s*$"
)

# Strip ops commentary from labels
_ARROW_NOTE = re.compile(r"\s*←.*$")
_PLUS_PAREN = re.compile(r"\s*\+\s*\([^)]*\)")
_WEEKS_PAREN = re.compile(r"\s*\([^)]*\bweeks?\b[^)]*\)", re.IGNORECASE)
_WEEKDAY_PAREN = re.compile(
    r"\s*\((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|"
    r"Thursday|Friday|Saturday|Sunday)[^)]*\)",
    re.IGNORECASE,
)
_BEFORE_AFTER_PAREN = re.compile(
    r"\s*\([^)]*\b(?:before|after)\b[^)]*\)",
    re.IGNORECASE,
)
# Trailing parenthetical of any kind (after week/weekday/before strips)
_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)\s*$")
# Long Confluence prose: "Sheets … which requires Math …"
_PROSE_TAIL = re.compile(
    r"\s+(?:which|that)\s+(?:requires?|needs?|includes?|will)\b.*$",
    re.IGNORECASE,
)
# "for English version only" / "for English only"
_ENGLISH_ONLY = re.compile(
    r"\s+for\s+English(?:\s+version)?\s+only\s*$",
    re.IGNORECASE,
)
# Soft max length for ticket titles (look density)
_PHASE_NAME_MAX = 42


@dataclass
class RoadmapPhaseLine:
    """One Confluence date line → one date ticket."""

    name: str
    date_desc: str  # passed to print_ticket -d / description
    kind: str  # "range" | "point"
    raw_line: str = ""


@dataclass
class ParsedRoadmap:
    product_name: str
    product_code: str  # may be empty
    phases: list[RoadmapPhaseLine] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def parse_product_title(title: str) -> tuple[str, str]:
    """
    Title field → (product_name, product_code).

    Accepts::
      27BG-111 - The Castaway
      The Castaway (27BG-111)
      The Castaway
    """
    t = (title or "").strip()
    if not t:
        return "", ""
    m = _TITLE_CODE_NAME.match(t)
    if m:
        return m.group("name").strip(), m.group("code").strip()
    m = _TITLE_NAME_CODE.match(t)
    if m:
        return m.group("name").strip(), m.group("code").strip()
    return t, ""


def clean_phase_label(label: str) -> str:
    """
    Reduce Confluence phase labels to short ticket names.

    Drops week counts, ← notes, holiday add-ons, trailing parentheticals,
    ``which requires…`` prose tails, and trims overlong titles.
    """
    s = (label or "").strip()
    s = _ARROW_NOTE.sub("", s)
    s = _PLUS_PAREN.sub("", s)
    s = _WEEKS_PAREN.sub("", s)
    s = _WEEKDAY_PAREN.sub("", s)
    s = _BEFORE_AFTER_PAREN.sub("", s)
    s = _PROSE_TAIL.sub("", s)
    s = _ENGLISH_ONLY.sub("", s)
    # Drop trailing parens repeatedly (after weeks/weekday already removed).
    # Strip trailing punct each pass so "(2 weeks)." does not block the next (…).
    while True:
        s = s.strip().rstrip(".,;: ")
        nxt = _TRAILING_PAREN.sub("", s).strip()
        if nxt == s:
            break
        s = nxt
    s = re.sub(r"\s+", " ", s).strip(" \t-–—:.,;")
    # Soft cap — cut on a word boundary
    if len(s) > _PHASE_NAME_MAX:
        cut = s[:_PHASE_NAME_MAX].rsplit(" ", 1)[0].strip(" -–—:.,;")
        if len(cut) >= 12:
            s = cut
    return s


def _is_date_token(s: str) -> bool:
    return bool(_DATE_RE.match((s or "").strip()))


def parse_confluence_date_list(body: str) -> tuple[list[RoadmapPhaseLine], list[str]]:
    """
    Parse Confluence paste body into phase lines + free notes.

    Blank lines ignored. ``Note: …`` and unparseable lines → notes.
    """
    phases: list[RoadmapPhaseLine] = []
    notes: list[str] = []
    text = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("note:") or low.startswith("notes:"):
            notes.append(line.split(":", 1)[-1].strip() or line)
            continue
        if ":" not in line:
            notes.append(line)
            continue
        left, right = line.split(":", 1)
        left, right = left.strip(), right.strip()
        if not right:
            notes.append(line)
            continue
        name = clean_phase_label(right)
        if not name:
            notes.append(line)
            continue
        rm = _RANGE_RE.match(left)
        if rm:
            start, end = rm.group(1).strip(), rm.group(2).strip()
            date_desc = f"{start} - {end}"
            phases.append(
                RoadmapPhaseLine(
                    name=name,
                    date_desc=date_desc,
                    kind="range",
                    raw_line=line,
                )
            )
            continue
        if _is_date_token(left):
            phases.append(
                RoadmapPhaseLine(
                    name=name,
                    date_desc=left,
                    kind="point",
                    raw_line=line,
                )
            )
            continue
        notes.append(line)
    return phases, notes


def parse_roadmap_blob(*, title: str, body: str) -> ParsedRoadmap:
    name, code = parse_product_title(title)
    phases, notes = parse_confluence_date_list(body)
    return ParsedRoadmap(
        product_name=name or "Untitled Title",
        product_code=code,
        phases=phases,
        notes=notes,
    )


def product_bin_title(parsed: ParsedRoadmap) -> str:
    if parsed.product_code:
        return f"{parsed.product_code} - {parsed.product_name}"
    return parsed.product_name


def materialize_roadmap_on_floor(
    world: World,
    *,
    title: str,
    body: str,
) -> tuple[str, dict[str, Any]]:
    """
    Spawn product bin + Production Dates + tickets at the player place.

    Returns (message, meta) where meta has product_id, dates_id, ticket_count.
    """
    from . import format as fmt
    from .ids import display_name

    parsed = parse_roadmap_blob(title=title, body=body)
    if not (title or "").strip():
        return (
            fmt.err(
                "Roadmap needs a product title  "
                "(studio Title: e.g. 27BG-111 - The Castaway)."
            ),
            {},
        )
    if not parsed.phases:
        return (
            fmt.err(
                "No date lines found in the body.  "
                "Paste Confluence lines like:\n"
                "  Nov 17, 2025 - Dec 15, 2025: Design Phase (4 weeks)"
            ),
            {},
        )

    loc = world.player_location()
    if loc is None:
        return fmt.err("Nowhere to spawn — go somewhere first."), {}

    bin_name = product_bin_title(parsed)
    # Product shell
    product_ven = world.create_ven(
        bin_name,
        "bin",
        description=(
            f"Roadmap product card · {parsed.product_name}"
            + (f" · {parsed.product_code}" if parsed.product_code else "")
        ),
        tags=["roadmap", "title", "product"],
    )
    product_id = world.instantiate(
        product_ven,
        name_override=bin_name,
        description_override=(
            f"Title card for {parsed.product_name}.\n"
            f"Move into the right quarter / month bin when ready.\n"
            + (
                "Notes:\n" + "\n".join(f"- {n}" for n in parsed.notes) + "\n"
                if parsed.notes
                else ""
            )
        ),
        realm_instance_id=loc.realm_instance_id,
        timeline_instance_id=loc.timeline_instance_id,
    )
    world.put_in(product_id, loc.id, slot="interior")

    dates_ven = world.create_ven(
        "Production Dates",
        "bin",
        description="Phase and milestone date tickets for this title.",
        tags=["roadmap", "calendar", "dates"],
    )
    dates_id = world.instantiate(
        dates_ven,
        name_override="Production Dates",
        description_override="Imported from Confluence date list.",
        realm_instance_id=loc.realm_instance_id,
        timeline_instance_id=loc.timeline_instance_id,
    )
    world.put_in(dates_id, product_id, slot="interior")

    codes: list[str] = []
    for ph in parsed.phases:
        try:
            _iid, code = world.print_ticket(
                name=ph.name,
                subtype="date",
                kind=ph.kind,
                description=ph.date_desc,
                into_instance_id=dates_id,
            )
            codes.append(code)
        except ValueError:
            continue

    # Optional place lore/record for blob notes — skip if empty
    if parsed.notes:
        try:
            world.add_lore(
                "instance",
                product_id,
                body="\n".join(parsed.notes),
                title="Import notes",
                author="roadmap import",
            )
        except Exception:  # noqa: BLE001
            pass

    product = world.get_instance(product_id)
    pname = display_name(product.name) if product else bin_name
    try:
        pref = world.short_ref_of(product_id)
    except Exception:  # noqa: BLE001
        pref = product_id[:12]

    lines = [
        fmt.ok(
            f"Roadmap imported · {pname}  ·  {len(codes)} date ticket(s)"
        ),
        fmt.hint(f"  product  {pref}  ·  on floor here — put into quarter/month"),
        fmt.hint("  holds  Production Dates  (tickets inside)"),
    ]
    if parsed.notes:
        lines.append(fmt.hint(f"  notes  {len(parsed.notes)}  (on product record)"))
    if len(codes) < len(parsed.phases):
        lines.append(
            fmt.hint(
                f"  skipped {len(parsed.phases) - len(codes)} line(s) that failed to print"
            )
        )
    # Sample of first few phases
    for ph in parsed.phases[:4]:
        lines.append(fmt.hint(f"    · {ph.name}  ·  {ph.date_desc}"))
    if len(parsed.phases) > 4:
        lines.append(fmt.hint(f"    · … +{len(parsed.phases) - 4} more"))

    meta = {
        "product_id": product_id,
        "dates_id": dates_id,
        "ticket_count": len(codes),
        "ticket_codes": codes,
        "product_name": parsed.product_name,
        "product_code": parsed.product_code,
    }
    return fmt.join_blocks(*lines, gap=0), meta
