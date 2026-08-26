"""
WDC App — Student Router
All endpoints require an authenticated student.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..auth import get_current_user, require_role
from ..schemas import RegistrationOut, AttendanceOut, NotificationOut
from ..services import db, audit

router = APIRouter(prefix="/api/me", tags=["student"])


def _ensure_student(user):
    if user.get("role") != "Student":
        raise HTTPException(403, "Student-only endpoint")
    return user


@router.get("")
def me(user=Depends(get_current_user)):
    _ensure_student(user)
    return {
        "id": user["id"],
        "name": user.get("name"),
        "email": user["email"],
        "department": user.get("department"),
        "class_year": user.get("class_year"),
        "role": user.get("role"),
    }


@router.get("/events", response_model=List[RegistrationOut])
def my_events(user=Depends(get_current_user)):
    _ensure_student(user)
    regs = db.list("registrations", where={"student_id": user["id"]})
    out = []
    for r in regs:
        e = db.get("events", r.get("event_id", ""))
        out.append(RegistrationOut(
            id=r["id"],
            event_id=r["event_id"],
            event_title=e.get("title", "") if e else "(deleted event)",
            event_date=e.get("date") if e else None,
            status=r.get("status", "registered"),
        ))
    return out


@router.post("/events/{event_id}/register", response_model=RegistrationOut)
def register(event_id: str, user=Depends(get_current_user)):
    _ensure_student(user)
    event = db.get("events", event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    if event.get("status") != "published":
        raise HTTPException(400, "Event not open for registration")
    if not event.get("registration_enabled", True):
        raise HTTPException(400, "Registration is closed for this event")

    # check target audience
    target_depts = event.get("target_departments") or []
    if target_depts and user.get("department") not in target_depts:
        raise HTTPException(403, "Your department is not eligible for this event")
    target_classes = event.get("target_classes") or []
    if target_classes and user.get("class_year") not in target_classes:
        raise HTTPException(403, "Your class is not eligible for this event")

    existing = db.list("registrations", where={"event_id": event_id, "student_id": user["id"]})
    existing = [r for r in existing if r.get("status") in ("registered", "waitlisted")]
    if existing:
        raise HTTPException(409, "Already registered")

    # capacity check
    regs = [r for r in db.list("registrations", where={"event_id": event_id}) if r.get("status") == "registered"]
    capacity = event.get("capacity") or 0
    status = "registered"
    if capacity and len(regs) >= capacity:
        status = "waitlisted"

    reg = db.insert("registrations", {
        "event_id": event_id,
        "student_id": user["id"],
        "status": status,
        "registered_at": None,
    })
    audit(user["id"], "register_event", event_id)
    return RegistrationOut(
        id=reg["id"],
        event_id=event_id,
        event_title=event.get("title", ""),
        event_date=event.get("date"),
        status=status,
    )


@router.delete("/events/{event_id}/register")
def cancel_registration(event_id: str, user=Depends(get_current_user)):
    _ensure_student(user)
    regs = db.list("registrations", where={"event_id": event_id, "student_id": user["id"]})
    if not regs:
        raise HTTPException(404, "No registration to cancel")
    reg = regs[0]
    db.update("registrations", reg["id"], {"status": "cancelled"})
    audit(user["id"], "cancel_registration", event_id)
    return {"ok": True, "message": "Registration cancelled"}


@router.get("/attendance", response_model=List[AttendanceOut])
def my_attendance(user=Depends(get_current_user)):
    _ensure_student(user)
    rows = db.list("attendance", where={"student_id": user["id"]})
    out = []
    for a in rows:
        e = db.get("events", a.get("event_id", ""))
        out.append(AttendanceOut(
            id=a["id"],
            event_id=a["event_id"],
            event_title=e.get("title", "") if e else "(deleted)",
            event_date=e.get("date") if e else None,
            status=a.get("status", "absent"),
        ))
    return out


@router.get("/notifications", response_model=List[NotificationOut])
def my_notifications(user=Depends(get_current_user)):
    _ensure_student(user)
    rows = db.list("notifications", where={"user_id": user["id"]})
    # also include broadcast notifications (user_id == None or "all")
    rows += db.list("notifications", where={"user_id": "all"})
    rows.sort(key=lambda n: n.get("created_at", ""), reverse=True)
    return [NotificationOut(
        id=n["id"],
        title=n.get("title", ""),
        body=n.get("body", ""),
        created_at=n.get("created_at", ""),
        read=n.get("read", False),
        channel=n.get("channel", "in_app"),
    ) for n in rows]


@router.post("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: str, user=Depends(get_current_user)):
    _ensure_student(user)
    n = db.get("notifications", notif_id)
    if not n:
        raise HTTPException(404, "Notification not found")
    if n.get("user_id") not in (user["id"], "all", None):
        raise HTTPException(403, "Not yours")
    db.update("notifications", notif_id, {"read": True})
    return {"ok": True}
