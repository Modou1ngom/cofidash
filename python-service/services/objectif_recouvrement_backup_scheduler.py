"""
Robot de l'objectif de recouvrement.

Le mois en cours est enregistré s'il n'a pas encore de photo.
Ensuite, chaque 1er du mois à 06:00, le nouveau mois est figé.
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


def _run(year: int, month: int) -> None:
    global _running_job
    with _lock:
        if _running_job:
            logger.warning("Sauvegarde objectif recouvrement déjà en cours, skip")
            return
        _running_job = True
    try:
        from services.objectif_recouvrement_backup_service import refresh_objectif_recouvrement

        result = refresh_objectif_recouvrement(year, month)
        logger.info("Job objectif recouvrement terminé: %s", result)
    except Exception as exc:
        logger.error("Job objectif recouvrement échoué: %s", exc, exc_info=True)
    finally:
        with _lock:
            _running_job = False


def _run_current_if_missing() -> None:
    today = datetime.now()
    try:
        from services.objectif_recouvrement_backup_service import has_objectif_recouvrement_snapshot

        if has_objectif_recouvrement_snapshot(today.year, today.month):
            logger.info(
                "Objectif recouvrement %04d-%02d déjà en base",
                today.year,
                today.month,
            )
            return
    except Exception as exc:
        logger.error("Lecture objectif recouvrement échouée: %s", exc, exc_info=True)
        return
    _run(today.year, today.month)


def _loop() -> None:
    logger.info("Robot objectif recouvrement démarré (photo du mois, puis chaque 1er à 06:00)")
    threading.Thread(
        target=_run_current_if_missing,
        name="objectif-recouvrement-backup-job",
        daemon=True,
    ).start()
    while not _stop_event.is_set():
        nxt = next_run_at()
        wait_s = max(1.0, (nxt - datetime.now()).total_seconds())
        logger.info(
            "Prochaine sauvegarde objectif recouvrement à %s (dans %.0f s)",
            nxt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_s,
        )
        if _stop_event.wait(timeout=wait_s):
            break
        today = datetime.now()
        threading.Thread(
            target=_run,
            args=(today.year, today.month),
            name="objectif-recouvrement-backup-job",
            daemon=True,
        ).start()
        if _stop_event.wait(timeout=60):
            break


def start_objectif_recouvrement_scheduler() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_loop,
        name="objectif-recouvrement-backup-scheduler",
        daemon=True,
    )
    _thread.start()


def stop_objectif_recouvrement_scheduler() -> None:
    _stop_event.set()
