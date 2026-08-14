"""
Planificateur : fige les objectifs EPV vue le 1er de chaque mois à 06:00.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
_running_job = False


def next_run_at(now: Optional[datetime] = None) -> datetime:
    """Prochain 1er du mois à 06:00."""
    now = now or datetime.now()
    candidate = datetime(now.year, now.month, 1, 6, 0, 0)
    if candidate > now:
        return candidate
    if now.month == 12:
        return datetime(now.year + 1, 1, 1, 6, 0, 0)
    return datetime(now.year, now.month + 1, 1, 6, 0, 0)


def _run_backup_safe() -> None:
    global _running_job
    with _lock:
        if _running_job:
            logger.warning("Snapshot objectifs EPV vue déjà en cours, skip")
            return
        _running_job = True
    try:
        from services.objectif_epv_vue_backup_service import refresh_objectif_epv_vue_snapshot

        today = datetime.now()
        result = refresh_objectif_epv_vue_snapshot(month=today.month, year=today.year)
        logger.info("Job objectifs EPV vue terminé: %s", result)
    except Exception as exc:
        logger.error("Job objectifs EPV vue échoué: %s", exc, exc_info=True)
    finally:
        with _lock:
            _running_job = False


def _loop() -> None:
    logger.info("Planificateur objectifs EPV vue démarré (1er du mois à 06:00)")
    while not _stop_event.is_set():
        nxt = next_run_at()
        wait_s = max(1.0, (nxt - datetime.now()).total_seconds())
        logger.info(
            "Prochain snapshot objectifs EPV vue à %s (dans %.0f s)",
            nxt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_s,
        )
        if _stop_event.wait(timeout=wait_s):
            break
        threading.Thread(
            target=_run_backup_safe,
            name="objectif-epv-vue-backup-job",
            daemon=True,
        ).start()
        if _stop_event.wait(timeout=60):
            break


def start_objectif_epv_vue_scheduler() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_loop,
        name="objectif-epv-vue-backup-scheduler",
        daemon=True,
    )
    _thread.start()


def stop_objectif_epv_vue_scheduler() -> None:
    _stop_event.set()
