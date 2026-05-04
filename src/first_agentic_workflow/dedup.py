"""SQLite-based lead deduplication."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import aiosqlite

if TYPE_CHECKING:
    from pathlib import Path

    from first_agentic_workflow.models import RawLead

_SUFFIX_RE = re.compile(
    r"\s*,?\s*\b(inc|llc|ltd|limited|corp|corporation|co|company|group|plc)\.?\s*$",
    re.IGNORECASE,
)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name_normalized TEXT NOT NULL,
    website_domain TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    UNIQUE(company_name_normalized, website_domain)
)
"""


def normalize_company_name(name: str) -> str:
    """Lowercase and strip common corporate suffixes."""
    return _SUFFIX_RE.sub("", name).strip().lower()


def extract_domain(url: str | None) -> str | None:
    """Extract the domain from a URL, stripping www prefix."""
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.hostname or ""
    return domain.removeprefix("www.").lower() or None


class Deduplicator:
    """Check and track leads to avoid re-processing duplicates."""

    def __init__(self) -> None:
        self._db: aiosqlite.Connection | None = None

    async def init_db(self, db_path: Path) -> None:
        """Open the SQLite database and create tables if needed."""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(db_path))
        await self._db.execute(_CREATE_TABLE)
        await self._db.commit()

    def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "Database not initialized. Call init_db() first."
            raise RuntimeError(msg)
        return self._db

    async def is_known(self, lead: RawLead) -> bool:
        """Return True if this lead has been seen before."""
        db = self._get_db()
        name = normalize_company_name(lead.company_name)
        domain = extract_domain(lead.website)
        cursor = await db.execute(
            "SELECT 1 FROM leads WHERE company_name_normalized = ? AND website_domain IS ?",
            (name, domain),
        )
        row = await cursor.fetchone()
        if row:
            now = datetime.now().isoformat()
            await db.execute(
                "UPDATE leads SET last_seen = ? "
                "WHERE company_name_normalized = ? AND website_domain IS ?",
                (now, name, domain),
            )
            await db.commit()
        return row is not None

    async def mark_seen(self, lead: RawLead) -> None:
        """Record a lead as seen."""
        db = self._get_db()
        name = normalize_company_name(lead.company_name)
        domain = extract_domain(lead.website)
        now = datetime.now().isoformat()
        await db.execute(
            "INSERT OR IGNORE INTO leads "
            "(company_name_normalized, website_domain, first_seen, last_seen) "
            "VALUES (?, ?, ?, ?)",
            (name, domain, now, now),
        )
        await db.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
