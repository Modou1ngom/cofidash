"""
Planificateur New Deal : rafraîchit le snapshot à 06:00 et 12:00.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

RUN_HOURS: Tuple[int, ...] = (6, 12)

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
_running_job = False


def next_run_at(now: Optional[datetime] = None) -> datetime:
    now = now or datetime.now()
    for day_offset in range(0, 3):
        day = (now + timedelta(days=day_offset)).date()
        for hour in RUN_HOURS:
            candidate = datetime(day.year, day.month, day.day, hour, 0, 0)
            if candidate > now:
                return candidate
    return now + timedelta(hours=12)


def _run_backup_safe() -> None:
    global _running_job
    with _lock:
        if _running_job:
            logger.warning("Sauvegarde New Deal déjà en cours, skip")
            return
        _running_job = True
    try:
        from services.new_deal.backup_service import refresh_new_deal_snapshot

        result = refresh_new_deal_snapshot()
        logger.info("Job New Deal terminé: %s", result)
    except Exception as exc:
        logger.error("Job New Deal échoué: %s", exc, exc_info=True)
    finally:
        with _lock:
            _running_job = False


def _loop() -> None:
    logger.info(
        "Planificateur New Deal démarré (heures: %s)",
        ", ".join(f"{h:02d}:00" for h in RUN_HOURS),
    )
    while not _stop_event.is_set():
        nxt = next_run_at()
        wait_s = max(1.0, (nxt - datetime.now()).total_seconds())
        logger.info(
            "Prochaine sauvegarde New Deal à %s (dans %.0f s)",
            nxt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_s,
        )
        if _stop_event.wait(timeout=wait_s):
            break
        threading.Thread(
            target=_run_backup_safe,
            name="new-deal-backup-job",
            daemon=True,
        ).start()
        if _stop_event.wait(timeout=60):
            break


def start_backup_scheduler() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_loop,
        name="new-deal-backup-scheduler",
        daemon=True,
    )
    _thread.start()


def stop_backup_scheduler() -> None:
    _stop_event.set()
