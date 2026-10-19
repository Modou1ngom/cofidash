"""
Robot de sauvegarde du suivi échéance.

La photo est rafraîchie toutes les 30 minutes (:00 et :30) et remplace la précédente.
Au démarrage, une passe part tout de suite si la dernière photo a plus de 30 minutes.
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


def _run() -> None:
    global _running_job
    with _lock:
        if _running_job:
            logger.warning("Sauvegarde suivi échéance déjà en cours, skip")
            return
        _running_job = True
    try:
        from services.suivi_echeance_backup_service import refresh_suivi_echeance_day

        result = refresh_suivi_echeance_day()
        logger.info("Job sauvegarde suivi échéance terminé: %s", result)
    except Exception as exc:
        logger.error("Job sauvegarde suivi échéance échoué: %s", exc, exc_info=True)
    finally:
        with _lock:
            _running_job = False


def _loop() -> None:
    logger.info(
        "Robot suivi échéance démarré (toutes les %s minutes)",
        INTERVAL_MINUTES,
    )
    threading.Thread(
        target=_run,
        name="suivi-echeance-backup-job",
        daemon=True,
    ).start()

    while not _stop_event.is_set():
        nxt = next_run_at()
        wait_s = max(1.0, (nxt - datetime.now()).total_seconds())
        logger.info(
            "Prochaine sauvegarde suivi échéance à %s (dans %.0f s)",
            nxt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_s,
        )
        if _stop_event.wait(timeout=wait_s):
            break
        threading.Thread(
            target=_run,
            name="suivi-echeance-backup-job",
            daemon=True,
        ).start()
        if _stop_event.wait(timeout=5):
            break


def start_suivi_echeance_scheduler() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_loop,
        name="suivi-echeance-backup-scheduler",
        daemon=True,
    )
    _thread.start()


def stop_suivi_echeance_scheduler() -> None:
    _stop_event.set()
