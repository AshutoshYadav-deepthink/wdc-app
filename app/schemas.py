"""
WDC App — Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class StudentSignup(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    department: str  # BSc IT | BMS | BAF | BCom
    class_year: str  # FY/SY/TY-prefixed class code e.g. FYBSc IT


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: Optional[str] = None


# ---------- Public ----------
class EventOut(BaseModel):
    id: str
    title: str
    slug: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    venue: Optional[str] = None
    capacity: Optional[int] = None
    topics: List[str] = []
    status: str = "published"
    cover_image_url: Optional[str] = None
    speaker_name: Optional[str] = None
    registered_count: int = 0


# ---------- Student ----------
class RegistrationOut(BaseModel):
    id: str
    event_id: str
    event_title: str
    event_date: Optional[str] = None
    status: str


class AttendanceOut(BaseModel):
    id: str
    event_id: str
    event_title: str
    event_date: Optional[str] = None
    status: str


class NotificationOut(BaseModel):
    id: str
    title: str
    body: str
    created_at: str
    read: bool = False
    channel: str = "in_app"


# ---------- Admin: Events ----------
class EventCreate(BaseModel):
    title: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = "lecture"
    women_date_id: Optional[str] = None
    date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    venue: Optional[str] = None
    capacity: Optional[int] = None
    registration_deadline: Optional[str] = None
    speaker_id: Optional[str] = None
    topics: List[str] = []
    target_departments: List[str] = []
    target_classes: List[str] = []
    status: str = "draft"
    registration_enabled: bool = True
    cover_image_url: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    venue: Optional[str] = None
    capacity: Optional[int] = None
    registration_deadline: Optional[str] = None
    speaker_id: Optional[str] = None
    topics: Optional[List[str]] = None
    target_departments: Optional[List[str]] = None
    target_classes: Optional[List[str]] = None
    status: Optional[str] = None
    registration_enabled: Optional[bool] = None
    cover_image_url: Optional[str] = None


# ---------- Admin: Attendance ----------
class AttendanceMark(BaseModel):
    event_id: str
    student_id: str
    status: str  # present | absent | late


class AttendanceImport(BaseModel):
    event_id: str
    records: List[AttendanceMark]


# ---------- Admin: Notifications ----------
class NotificationCreate(BaseModel):
    title: str
    body: str
    audience: str = "all"  # all | department | class | event
    audience_filter: Optional[str] = None  # e.g. "BSc IT" or event id
    channels: List[str] = ["in_app"]  # in_app | push | email
    scheduled_at: Optional[str] = None


# ---------- Admin: Users ----------
class RoleUpdate(BaseModel):
    role: str  # Super Admin | Admin | Coordinator | Staff | Student


# ---------- Reports ----------
class ReportOut(BaseModel):
    total_events: int
    published_events: int
    total_students: int
    total_registrations: int
    total_attendance_present: int
    events: List[dict] = []
