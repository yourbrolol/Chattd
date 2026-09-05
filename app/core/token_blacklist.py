"""JWT blacklist with lazy, singleflight auto-cleanup.

Design
------
1. Storage: ``revoked_tokens`` DB table. ``jti`` PK gives O(log N) lookups;
   indexed ``expires_at`` acts as the persistent min-heap/min-stack ordered
   by expiry, so finding/deleting expired rows never scans the whole table.
   No third-party blacklist library is used on purpose: ``python-jose`` /
   ``fastapi-jwt-auth`` style helpers only decode tokens — none ships a
   scalable persistent store, so stdlib ``asyncio`` + SQLAlchemy is the
   lightest correct solution.

2. Auto-cleanup: :func:`is_revoked` never blocks the current request on a
   purge. If the queried row turns out to be already expired it counts as
   "not revoked", and a background purge for *later* queries is scheduled.
   Overlapping purges are coalesced (singleflight): if a purge is already
   running, or one ran within ``CLEANUP_COOLDOWN_SECONDS``, new triggers
   return immediately — earlier queries' cleanup covers later ones.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Max rows removed per purge round; keeps each DELETE short even with
# a huge blacklist (index on expires_at makes each round O(batch log N)).
PURGE_BATCH_SIZE = 1000
# Minimum seconds between two background purges.
CLEANUP_COOLDOWN_SECONDS = 60.0

_cleanup_in_progress: bool = False
_last_cleanup: float = 0.0
_lock = asyncio.Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_naive_utc(dt: datetime) -> datetime:
    """DBs (sqlite) may return naive datetimes; compare in the same domain."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def revoke(db: AsyncSession, *, jti: str, expires_at: datetime, user_id: int | None = None) -> None:
    """Insert ``jti`` into the blacklist (idempotent)."""
    from app.chat.models import RevokedToken  # local import: avoid circulars

    if not jti:
        return
    db.add(RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at))
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        # Row already present (concurrent logout with same token) — not an error.
        logger.debug("revoke: jti %s already blacklisted", jti)


async def is_revoked(db: AsyncSession, jti: str | None) -> bool:
    """Return True iff ``jti`` is currently blacklisted.

    An entry whose ``expires_at`` has passed counts as expired (False), and
    schedules a background purge affecting *later* queries — the current
    call returns immediately without waiting for any DELETE.
    """
    from app.chat.models import RevokedToken

    if not jti:
        return False
    row = (await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))).scalars().first()
    if row is None:
        return False
    if _as_naive_utc(row.expires_at) <= _as_naive_utc(_utcnow()):
        _schedule_cleanup()
        return False
    return True


async def purge_expired(db: AsyncSession, *, batch_size: int = PURGE_BATCH_SIZE) -> int:
    """Delete expired rows in batches. Returns total rows removed."""
    from app.chat.models import RevokedToken

    total = 0
    while True:
        subq = select(RevokedToken.jti).where(RevokedToken.expires_at <= _utcnow()).limit(batch_size)
        res = await db.execute(delete(RevokedToken).where(RevokedToken.jti.in_(subq)))
        await db.commit()
        removed = res.rowcount or 0
        total += removed
        if removed < batch_size:
            break
    return total


async def _run_cleanup() -> None:
    """Background purge body. Singleflight via module-level flag + lock."""
    global _cleanup_in_progress, _last_cleanup
    async with _lock:
        if _cleanup_in_progress:
            return  # an earlier query's cleanup is still running — skip
        if time.monotonic() - _last_cleanup < CLEANUP_COOLDOWN_SECONDS:
            return  # ran recently — skip
        _cleanup_in_progress = True
    try:
        from app.core.database import SessionLocal  # local import: avoid circulars

        async with SessionLocal() as session:
            removed = await purge_expired(session)
        _last_cleanup = time.monotonic()
        logger.debug("token blacklist purge removed %d rows", removed)
    except Exception:
        logger.exception("token blacklist purge failed")
    finally:
        _cleanup_in_progress = False


def _schedule_cleanup() -> None:
    """Fire-and-forget purge for *later* queries; never blocks the caller."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # no loop (e.g. sync context) — next async query will retry
    loop.create_task(_run_cleanup())
