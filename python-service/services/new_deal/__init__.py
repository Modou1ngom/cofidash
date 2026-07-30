"""
Package New Deal : snapshot Flexcube → SQLite, planificateur 06h/12h, lecture CAF.
"""
from services.new_deal.backup_scheduler import (
    start_backup_scheduler,
    stop_backup_scheduler,
)
from services.new_deal.backup_service import (
    get_new_deal_for_caf,
    init_new_deal_local_db,
    read_new_deal_rows,
    refresh_new_deal_snapshot,
)
from services.new_deal.service import get_new_deal_data

__all__ = [
    "get_new_deal_data",
    "get_new_deal_for_caf",
    "init_new_deal_local_db",
    "read_new_deal_rows",
    "refresh_new_deal_snapshot",
    "start_backup_scheduler",
    "stop_backup_scheduler",
]
