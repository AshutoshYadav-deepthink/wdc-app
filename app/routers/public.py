"""
WDC App — Public Router (no auth)
GET /api/events          — list published events
GET /api/events/{id}     — single event detail
Also serves women_dates for the public dashboard.
"""
from fastapi import APIRouter, HTTPException
from typing import List

from ..schemas import EventOut
from ..services import db

router = APIRouter(prefix="/api", tags=["public"])


def _event_to_out(e: dict, include_count: bool = True) -> dict:
    speaker = None
    if e.get("speaker_id"):
        s = db.get("speakers", e["speaker_id"])
        if s:
            speaker = s.get("name")
    reg_count = 0
    if include_count:
        regs = db.list("registrations", where={"event_id": e["id"]})
        reg_count = sum(1 for r in regs if r.get("status") == "registered")
    return EventOut(
        id=e["id"],
        title=e.get("title", ""),
        slug=e.get("slug", e["id"]),
        short_description=e.get("short_description"),
        description=e.get("description"),
        event_type=e.get("event_type"),
        date=e.get("date"),
        start_time=e.get("start_time"),
        end_time=e.get("end_time"),
        venue=e.get("venue"),
        capacity=e.get("capacity"),
        topics=e.get("topics", []) or [],
        status=e.get("status", "published"),
        cover_image_url=e.get("cover_image_url"),
        speaker_name=speaker,
        registered_count=reg_count,
    ).model_dump()


@router.get("/events", response_model=List[dict])
def list_events():
    events = db.list("events")
    published = [e for e in events if e.get("status") == "published"]
    # newest first
    published.sort(key=lambda e: e.get("date", ""), reverse=True)
    return [_event_to_out(e) for e in published]


@router.get("/events/{event_id}", response_model=dict)
def get_event(event_id: str):
    e = db.get("events", event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    if e.get("status") not in ("published", "completed"):
        # don't expose drafts/cancelled publicly
        raise HTTPException(404, "Event not found")
    return _event_to_out(e)


@router.get("/women-dates")
def list_women_dates():
    rows = db.list("women_dates")
    rows.sort(key=lambda r: (r.get("month", 0), r.get("day", 0)))
    return rows


@router.get("/speakers")
def list_speakers():
    return db.list("speakers")
