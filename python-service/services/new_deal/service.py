"""
Lecture New Deal — snapshot SQLite alimenté depuis Flexcube (06h / 12h).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from services.new_deal.backup_service import read_new_deal_rows


def get_new_deal_data(limit: Optional[int] = None) -> Dict[str, Any]:
    return read_new_deal_rows(limit=limit)
