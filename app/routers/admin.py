"""
WDC App — Admin Router
All endpoints require an authenticated staff role (Super Admin / Admin / Coordinator / Staff)
with appropriate permission.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..auth import get_current_user, require_permission
from ..schemas import (
    EventCreate, EventUpdate, AttendanceMark, AttendanceImport,
    NotificationCreate, RoleUpdate, ReportOut,
)
from ..services import db, audit, user_has_permission, ROLES, ROLE_PERMISSIONS

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------- Events ----------
@router.get("/events")
def admin_list_events(user=Depends(require_permission("MANAGE_EVENTS"))):
    events = db.list("events")
    events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    # include registration count
    for e in events:
        regs = [r for r in db.list("registrations", where={"event_id": e["id"]}) if r.get("status") == "registered"]
        e["registered_count"] = len(regs)
    return events


@router.post("/events")
def create_event(payload: EventCreate, user=Depends(require_permission("MANAGE_EVENTS"))):
    slug = payload.title.lower().replace(" ", "-").replace("/", "-")[:60]
    doc = payload.model_dump()
    doc["slug"] = slug
    doc["created_by"] = user["id"]
    ev = db.insert("events", doc)
    audit(user["id"], "create_event", ev["id"])
    return ev


@router.patch("/events/{event_id}")
def update_event(event_id: str, payload: EventUpdate, user=Depends(require_permission("MANAGE_EVENTS"))):
    e = db.get("events", event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    patch = payload.model_dump(exclude_none=True)
    updated = db.update("events", event_id, patch)
    audit(user["id"], "update_event", event_id)
    return updated


@router.delete("/events/{event_id}")
def delete_event(event_id: str, user=Depends(require_permission("MANAGE_EVENTS"))):
    e = db.get("events", event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    # Archive rather than hard delete if there are registrations
    regs = db.list("registrations", where={"event_id": event_id})
    if regs:
        db.update("events", event_id, {"status": "cancelled"})
        audit(user["id"], "archive_event", event_id)
        return {"ok": True, "archived": True}
    db.delete("events", event_id)
    audit(user["id"], "delete_event", event_id)
    return {"ok": True, "deleted": True}


@router.get("/events/{event_id}/participants")
def event_participants(event_id: str, user=Depends(require_permission("MANAGE_REGISTRATIONS"))):
    e = db.get("events", event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    regs = db.list("registrations", where={"event_id": event_id})
    out = []
    for r in regs:
        if r.get("status") not in ("registered", "waitlisted"):
            continue
        s = db.get("users", r.get("student_id", ""))
        out.append({
            "registration_id": r["id"],
            "student_id": r.get("student_id"),
            "name": s.get("name") if s else None,
            "email": s.get("email") if s else None,
            "department": s.get("department") if s else None,
            "class_year": s.get("class_year") if s else None,
            "status": r.get("status"),
            "registered_at": r.get("created_at"),
        })
    return out


# ---------- Speakers ----------
@router.get("/speakers")
def list_speakers(user=Depends(get_current_user)):
    return db.list("speakers")


@router.post("/speakers")
def create_speaker(payload: dict, user=Depends(require_permission("MANAGE_SPEAKERS"))):
    return db.insert("speakers", payload)


# ---------- Attendance ----------
@router.post("/attendance")
def mark_attendance(payload: AttendanceMark, user=Depends(require_permission("MANAGE_ATTENDANCE"))):
    existing = db.list("attendance", where={"event_id": payload.event_id, "student_id": payload.student_id})
    if existing:
        rec = db.update("attendance", existing[0]["id"], {"status": payload.status})
    else:
        rec = db.insert("attendance", {
            "event_id": payload.event_id,
            "student_id": payload.student_id,
            "status": payload.status,
        })
    audit(user["id"], "mark_attendance", rec["id"])
    return rec


@router.post("/attendance/import")
def import_attendance(payload: AttendanceImport, user=Depends(require_permission("MANAGE_ATTENDANCE"))):
    created = 0
    for r in payload.records:
        existing = db.list("attendance", where={"event_id": payload.event_id, "student_id": r.student_id})
        if existing:
            db.update("attendance", existing[0]["id"], {"status": r.status})
        else:
            db.insert("attendance", {
                "event_id": payload.event_id,
                "student_id": r.student_id,
                "status": r.status,
            })
        created += 1
    audit(user["id"], "import_attendance", payload.event_id, {"count": created})
    return {"ok": True, "imported": created}


# ---------- Notifications ----------
@router.post("/notifications")
def send_notification(payload: NotificationCreate, user=Depends(require_permission("SEND_NOTIFICATIONS"))):
    audience = payload.audience
    targets: List[str] = []

    if audience == "all":
        targets = ["all"]
    elif audience == "department":
        if not payload.audience_filter:
            raise HTTPException(400, "audience_filter required for department audience")
        users = db.list("users", where={"role": "Student"})
        targets = [u["id"] for u in users if u.get("department") == payload.audience_filter]
    elif audience == "class":
        if not payload.audience_filter:
            raise HTTPException(400, "audience_filter required for class audience")
        users = db.list("users", where={"role": "Student"})
        targets = [u["id"] for u in users if u.get("class_year") == payload.audience_filter]
    elif audience == "event":
        if not payload.audience_filter:
            raise HTTPException(400, "audience_filter required for event audience")
        regs = db.list("registrations", where={"event_id": payload.audience_filter})
        targets = [r["student_id"] for r in regs if r.get("status") == "registered"]
    else:
        targets = ["all"]

    # If "all", store a single broadcast row
    if "all" in targets:
        notif = db.insert("notifications", {
            "user_id": "all",
            "title": payload.title,
            "body": payload.body,
            "channel": ",".join(payload.channels),
            "read": False,
        })
    else:
        notif = None
        for uid in targets:
            notif = db.insert("notifications", {
                "user_id": uid,
                "title": payload.title,
                "body": payload.body,
                "channel": ",".join(payload.channels),
                "read": False,
            })

    campaign = db.insert("notification_campaigns", {
        "title": payload.title,
        "body": payload.body,
        "audience": audience,
        "audience_filter": payload.audience_filter,
        "channels": payload.channels,
        "recipients": len(targets) if "all" not in targets else db.count("users", where={"role": "Student"}),
        "created_by": user["id"],
    })

    # Email stub: print to console (real SMTP wired via settings but optional)
    if "email" in payload.channels:
        from ..services.notifier import send_email
        send_email(
            to_list=["broadcast@wdc.local"],
            subject=payload.title,
            body=payload.body,
        )

    audit(user["id"], "send_notification", campaign["id"])
    return {"ok": True, "campaign_id": campaign["id"], "recipients": campaign["recipients"]}


# ---------- Users ----------
@router.get("/users")
def list_users(user=Depends(require_permission("MANAGE_USERS"))):
    users = db.list("users")
    return [{
        "id": u["id"],
        "email": u.get("email"),
        "name": u.get("name"),
        "role": u.get("role"),
        "department": u.get("department"),
        "class_year": u.get("class_year"),
        "active": u.get("active", True),
        "created_at": u.get("created_at"),
    } for u in users]


@router.patch("/users/{user_id}/role")
def change_user_role(user_id: str, payload: RoleUpdate, user=Depends(require_permission("CHANGE_USER_ROLE"))):
    if payload.role not in ROLES:
        raise HTTPException(400, "Invalid role")
    target = db.get("users", user_id)
    if not target:
        raise HTTPException(404, "User not found")
    # Special rule: only Super Admin can promote to Super Admin
    if payload.role == "Super Admin" and user.get("role") != "Super Admin":
        raise HTTPException(403, "Only Super Admin can grant Super Admin role")
    updated = db.update("users", user_id, {"role": payload.role})
    audit(user["id"], "change_role", user_id, {"from": target.get("role"), "to": payload.role})
    return updated


# ---------- Reports ----------
@router.get("/reports", response_model=ReportOut)
def reports(user=Depends(require_permission("VIEW_REPORTS"))):
    events = db.list("events")
    students = db.list("users", where={"role": "Student"})
    regs = db.list("registrations")
    att = db.list("attendance")
    present = [a for a in att if a.get("status") == "present"]

    event_stats = []
    for e in events:
        er = [r for r in regs if r.get("event_id") == e["id"] and r.get("status") == "registered"]
        ea = [a for a in att if a.get("event_id") == e["id"] and a.get("status") == "present"]
        event_stats.append({
            "id": e["id"],
            "title": e.get("title"),
            "date": e.get("date"),
            "status": e.get("status"),
            "registered": len(er),
            "present": len(ea),
        })

    return ReportOut(
        total_events=len(events),
        published_events=len([e for e in events if e.get("status") == "published"]),
        total_students=len(students),
        total_registrations=len([r for r in regs if r.get("status") == "registered"]),
        total_attendance_present=len(present),
        events=event_stats,
    )


# ---------- Women Dates ----------
@router.get("/women-dates")
def list_women_dates(user=Depends(get_current_user)):
    return db.list("women_dates")


@router.post("/women-dates")
def create_women_date(payload: dict, user=Depends(require_permission("MANAGE_EVENTS"))):
    return db.insert("women_dates", payload)


# ---------- Dashboard stats (admin landing) ----------
@router.get("/stats")
def admin_stats(user=Depends(get_current_user)):
    return {
        "total_events": db.count("events"),
        "published_events": db.count("events", where={"status": "published"}),
        "total_students": db.count("users", where={"role": "Student"}),
        "total_speakers": db.count("speakers"),
        "total_registrations": db.count("registrations", where={"status": "registered"}),
        "total_notifications_sent": db.count("notification_campaigns"),
    }
