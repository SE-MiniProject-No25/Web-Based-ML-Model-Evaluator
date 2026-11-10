"""When temporary artifacts are cleaned up (FR-17, SEC-07, TC-18).

Expired uploads are swept at start-up, after every submission, and on a timer
(``cleanup_interval_seconds``), so they do not wait for the next request. The files of an
evaluation that is still pending or running are never deleted, whatever their age.
"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def sweep_expired_artifacts(state) -> None:
    """Delete expired artifacts, keeping the files of unfinished evaluations."""
    try:
        state.storage.cleanup_expired(active_paths=state.results.active_paths())
    except Exception:  # a failed sweep must never take the service down; the next one retries
        logger.exception("Retention cleanup failed")


async def _sweep_periodically(app: FastAPI, interval: float) -> None:
    while True:
        await asyncio.sleep(interval)
        await asyncio.to_thread(sweep_expired_artifacts, app.state)


@contextlib.asynccontextmanager
async def retention_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Sweep at start-up, then every ``cleanup_interval_seconds`` until shutdown (0: no timer)."""
    await asyncio.to_thread(sweep_expired_artifacts, app.state)
    interval = app.state.settings.cleanup_interval_seconds
    timer = asyncio.create_task(_sweep_periodically(app, interval)) if interval > 0 else None
    try:
        yield
    finally:
        if timer is not None:
            timer.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await timer
