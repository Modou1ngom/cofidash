"""
Planificateur : snapshot transferts d'argent toutes les 30 minutes.

Rafraîchit le mois courant (tous opérateurs). Le mois précédent n'est
rechargé que s'il n'a pas encore de snapshot (typiquement en début de mois).
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

INTERVAL_MINUTES = 30

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
_running_job = False


def next_run_at(now: Optional[datetime] = None) -> datetime:
    """Prochaine occurrence :00 ou :30."""
    now = now or datetime.now()
    minute = 0 if now.minute < INTERVAL_MINUTES else INTERVAL_MINUTES
    candidate = now.replace(minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate = candidate + timedelta(minutes=INTERVAL_MINUTES)
    return candidate


def _run_backup_safe() -> None:
    global _running_job
    with _lock:
        if _running_job:
            logger.warning("Snapshot transferts déjà en cours, skip")
            return
        _running_job = True
    try:
        from services.transfers_backup_service import (
            has_transfers_snapshot,
            prev_month,
            refresh_transfers_snapshot,
            TRANSFER_SERVICES,
        )

        today = datetime.now()
        result = refresh_transfers_snapshot(month=today.month, year=today.year)
        logger.info("Job snapshot transferts (mois courant) terminé: %s", result)

        pm, py = prev_month(today.month, today.year)
        missing_prev = [
            svc for svc in TRANSFER_SERVICES if not has_transfers_snapshot(pm, py, svc)
        ]
        if missing_prev:
            prev = refresh_transfers_snapshot(month=pm, year=py)
            logger.info("Job snapshot transferts (M-1 manquant) terminé: %s", prev)
    except Exception as exc:
        logger.error("Job snapshot transferts échoué: %s", exc, exc_info=True)
    finally:
        with _lock:
            _running_job = False


def _loop() -> None:
    logger.info(
        "Planificateur transferts démarré (toutes les %s minutes)",
        INTERVAL_MINUTES,
    )
    while not _stop_event.is_set():
        nxt = next_run_at()
        wait_s = max(1.0, (nxt - datetime.now()).total_seconds())
        logger.info(
            "Prochain snapshot transferts à %s (dans %.0f s)",
            nxt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_s,
        )
        if _stop_event.wait(timeout=wait_s):
            break
        threading.Thread(
            target=_run_backup_safe,
            name="transfers-backup-job",
            daemon=True,
        ).start()
        if _stop_event.wait(timeout=5):
            break


def start_transfers_scheduler() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_loop,
        name="transfers-backup-scheduler",
        daemon=True,
    )
    _thread.start()


def stop_transfers_scheduler() -> None:
    _stop_event.set()
