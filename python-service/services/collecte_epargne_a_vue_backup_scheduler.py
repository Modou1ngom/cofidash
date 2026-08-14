"""
Planificateur : snapshot Collecte épargne à vue chaque jour à 06:00.

Le 1er du mois, fige d'abord les objectifs puis rafraîchit les données du mois.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

RUN_HOUR = 6

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
_running_job = False


def next_run_at(now: Optional[datetime] = None) -> datetime:
    """Prochaine occurrence à 06:00."""
    now = now or datetime.now()
    candidate = datetime(now.year, now.month, now.day, RUN_HOUR, 0, 0)
    if candidate > now:
        return candidate
    tomorrow = (now + timedelta(days=1)).date()
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, RUN_HOUR, 0, 0)


def _run_backup_safe() -> None:
    global _running_job
    with _lock:
        if _running_job:
            logger.warning("Snapshot collecte EPV vue déjà en cours, skip")
            return
        _running_job = True
    try:
        today = datetime.now()
        # 1er du mois : figer les objectifs avant le snapshot données
        if today.day == 1:
            try:
                from services.objectif_epv_vue_backup_service import (
                    refresh_objectif_epv_vue_snapshot,
                )

                obj = refresh_objectif_epv_vue_snapshot(
                    month=today.month, year=today.year
                )
                logger.info("Objectifs EPV vue figés (1er du mois): %s", obj)
            except Exception as exc:
                logger.error(
                    "Échec figement objectifs avant snapshot collecte: %s",
                    exc,
                    exc_info=True,
                )

        from services.collecte_epargne_a_vue_backup_service import (
            refresh_collecte_epv_vue_snapshot,
        )

        result = refresh_collecte_epv_vue_snapshot(
            month=today.month, year=today.year
        )
        logger.info("Job snapshot collecte EPV vue terminé: %s", result)
    except Exception as exc:
        logger.error("Job snapshot collecte EPV vue échoué: %s", exc, exc_info=True)
    finally:
        with _lock:
            _running_job = False


def _loop() -> None:
    logger.info("Planificateur collecte EPV vue démarré (tous les jours à %02d:00)", RUN_HOUR)
    while not _stop_event.is_set():
        nxt = next_run_at()
        wait_s = max(1.0, (nxt - datetime.now()).total_seconds())
        logger.info(
            "Prochain snapshot collecte EPV vue à %s (dans %.0f s)",
            nxt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_s,
        )
        if _stop_event.wait(timeout=wait_s):
            break
        threading.Thread(
            target=_run_backup_safe,
            name="collecte-epv-vue-backup-job",
            daemon=True,
        ).start()
        if _stop_event.wait(timeout=60):
            break


def start_collecte_epv_vue_scheduler() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_loop,
        name="collecte-epv-vue-backup-scheduler",
        daemon=True,
    )
    _thread.start()


def stop_collecte_epv_vue_scheduler() -> None:
    _stop_event.set()
