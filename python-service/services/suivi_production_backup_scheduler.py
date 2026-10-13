"""
Robot de sauvegarde du suivi de production.

Au démarrage, rejoue les années des trois dernières années qui n'ont pas
encore de photo du jour. Ensuite, tous les jours à 06:00, les trois années
sont sauvegardées à nouveau.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

RUN_HOUR = 6

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None


def next_run_at(now: Optional[datetime] = None) -> datetime:
    now = now or datetime.now()
    candidate = now.replace(hour=RUN_HOUR, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def _run(pending_only: bool) -> None:
    try:
        from services.suivi_production_backup_service import (
            refresh_suivi_production_history,
            refresh_suivi_production_pending,
        )

        if pending_only:
            result = refresh_suivi_production_pending()
        else:
            result = refresh_suivi_production_history()
        logger.info("Job sauvegarde suivi production terminé: %s", result)
    except Exception as exc:
        logger.error("Job sauvegarde suivi production échoué: %s", exc, exc_info=True)


def _loop() -> None:
    logger.info(
        "Robot suivi production démarré (3 dernières années, tous les jours à %02d:00)",
        RUN_HOUR,
    )
    threading.Thread(
        target=_run,
        args=(True,),
        name="suivi-production-backup-job",
        daemon=True,
    ).start()

    while not _stop_event.is_set():
        nxt = next_run_at()
        wait_s = max(1.0, (nxt - datetime.now()).total_seconds())
        logger.info(
            "Prochaine sauvegarde suivi production à %s (dans %.0f s)",
            nxt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_s,
        )
        if _stop_event.wait(timeout=wait_s):
            break
        threading.Thread(
            target=_run,
            args=(False,),
            name="suivi-production-backup-job",
            daemon=True,
        ).start()
        if _stop_event.wait(timeout=60):
            break


def start_suivi_production_scheduler() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_loop,
        name="suivi-production-backup-scheduler",
        daemon=True,
    )
    _thread.start()


def stop_suivi_production_scheduler() -> None:
    _stop_event.set()
