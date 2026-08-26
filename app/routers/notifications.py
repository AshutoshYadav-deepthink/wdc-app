"""
WDC App — Notifications router (public read endpoints wrapped here for organization)
The actual sending logic lives in admin.py (send_notification).
This file exposes a small helper router for student-side notification listing
convenience and re-exports the notifier.
"""
from fastapi import APIRouter, Depends
from ..auth import get_current_user
from ..services import db

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user=Depends(get_current_user)):
    rows = db.list("notifications", where={"user_id": user["id"]})
    rows += db.list("notifications", where={"user_id": "all"})
    rows.sort(key=lambda n: n.get("created_at", ""), reverse=True)
    return rows[:50]
