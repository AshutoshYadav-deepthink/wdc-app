"""
WDC App — Seed Data Loader
Populates the local DB with demo data per seed_data.json:
- 1 Super Admin
- 50-60 Students (split across BSc IT / BMS / BAF / BCom, FY/SY/TY)
- 5-10 Speakers
- 10-20 Events
- 10+ Women Dates
- A handful of registrations + attendance + notifications for demo realism
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .services import db
from .services.db import DEPARTMENTS, CLASSES
from .security import hash_password
from .config import settings


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def run_seed():
    # ---------- Women Dates ----------
    women_dates = [
        {"name": "National Girl Child Day", "month": 1, "day": 24},
        {"name": "International Day of Women and Girls in Science", "month": 2, "day": 11},
        {"name": "International Women's Day", "month": 3, "day": 8},
        {"name": "World Health Day", "month": 4, "day": 7},
        {"name": "International Day of the Midwife", "month": 5, "day": 5},
        {"name": "International Day of the Girl Child", "month": 10, "day": 11},
        {"name": "International Day for the Elimination of Violence against Women", "month": 11, "day": 25},
        {"name": "Human Rights Day", "month": 12, "day": 10},
        {"name": "National Women's Health Day", "month": 5, "day": 28},
        {"name": "Menstrual Hygiene Day", "month": 5, "day": 28},
        {"name": "Breast Cancer Awareness Day", "month": 10, "day": 19},
    ]
    for wd in women_dates:
        db.insert("women_dates", wd)

    # ---------- Super Admin ----------
    admin = db.insert("users", {
        "email": settings.default_super_admin_email,
        "password_hash": hash_password(settings.default_super_admin_password),
        "role": "Super Admin",
        "name": "WDC Super Admin",
        "department": None,
        "class_year": None,
        "active": True,
    })
    # also create a regular Admin for convenience
    db.insert("users", {
        "email": "coordinator@wdc.edu",
        "password_hash": hash_password("Coordinator@123"),
        "role": "Coordinator",
        "name": "WDC Coordinator",
        "department": None,
        "class_year": None,
        "active": True,
    })

    # ---------- Speakers ----------
    speakers = [
        {"name": "Dr. Anjali Mehta", "title": "Gynecologist", "organization": "City Hospital", "bio": "Women's health specialist with 15 years of experience."},
        {"name": "Adv. Priya Nair", "title": "Lawyer", "organization": "High Court Mumbai", "bio": "Women's rights and POCSO advocate."},
        {"name": "Ms. Sneha Kapoor", "title": "Counselor", "organization": "MindWell Clinic", "bio": "Mental health counselor focusing on young women."},
        {"name": "Dr. Reshma Shaikh", "title": "Professor", "organization": "Tata Institute", "bio": "Gender studies researcher."},
        {"name": "Dr. Kavita Rao", "title": "Oncologist", "organization": "Cancer Care Center", "bio": "Breast cancer screening specialist."},
        {"name": "Ms. Farida Khan", "title": "Entrepreneur", "organization": "Self-Help Groups Federation", "bio": "Financial literacy trainer."},
        {"name": "Insp. Meera Joshi", "title": "Police Inspector", "organization": "Women's Cell, Mumbai Police", "bio": "Cyber safety and women's helpline."},
        {"name": "Dr. Lakshmi Iyer", "title": "Nutritionist", "organization": "Wellness Clinic", "bio": "Adolescent nutrition expert."},
    ]
    speaker_ids = []
    for s in speakers:
        rec = db.insert("speakers", s)
        speaker_ids.append(rec["id"])

    # ---------- Students (50-60) ----------
    first_names = ["Aaradhya", "Saanvi", "Ananya", "Pooja", "Riya", "Diya", "Ishita", "Kavya",
                   "Sneha", "Nisha", "Priya", "Anjali", "Tanvi", "Shreya", "Meera", "Pallavi",
                   "Bhavya", "Trisha", "Roshni", "Fatima", "Zara", "Aisha", "Maryam", "Riya",
                   "Khushi", "Anika", "Sara", "Aditi", "Vani", "Diya", "Ira", "Mira",
                   "Naina", "Ritu", "Sonia", "Tara", "Uma", "Vaishali", "Wrida", "Yami"]
    last_names = ["Sharma", "Patel", "Iyer", "Khan", "Desai", "Pillai", "Mehta", "Shah",
                  "Nair", "Reddy", "Joshi", "Gupta", "Singh", "Rao", "Kapoor", "Malhotra"]

    student_count = 55
    student_ids = []
    random.seed(42)
    for i in range(student_count):
        dept = random.choice(DEPARTMENTS)
        cls = random.choice(CLASSES[dept])
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"student{i+1:02d}@wdc.edu"
        password = "Student@123"
        user = db.insert("users", {
            "email": email,
            "password_hash": hash_password(password),
            "role": "Student",
            "name": name,
            "department": dept,
            "class_year": cls,
            "active": True,
        })
        db.insert("students", {
            "user_id": user["id"],
            "name": name,
            "email": email,
            "department": dept,
            "class_year": cls,
        })
        student_ids.append(user["id"])

    # ---------- Events (10-20) ----------
    today = datetime.now(timezone.utc).date()
    event_templates = [
        {"title": "Women's Health & Hygiene Awareness Workshop", "type": "workshop",
         "desc": "Interactive workshop covering menstrual hygiene, nutrition, and preventive health checks.",
         "topics": ["Health", "Hygiene", "Nutrition"], "speaker_idx": 0},
        {"title": "Know Your Legal Rights — Women & Law", "type": "lecture",
         "desc": "Awareness session on Indian legal protections for women: DV Act, POCSO, workplace harassment.",
         "topics": ["Law", "Rights"], "speaker_idx": 1},
        {"title": "Mental Wellness Circle", "type": "session",
         "desc": "Safe space discussion on stress, anxiety, and coping strategies for college women.",
         "topics": ["Mental Health", "Wellness"], "speaker_idx": 2},
        {"title": "Gender Sensitization Seminar", "type": "seminar",
         "desc": "Understanding gender biases in academia and workplace.",
         "topics": ["Gender", "Sensitization"], "speaker_idx": 3},
        {"title": "Breast Cancer Awareness & Screening Drive", "type": "drive",
         "desc": "Awareness talk followed by free screening camp for students and staff.",
         "topics": ["Health", "Cancer"], "speaker_idx": 4},
        {"title": "Financial Literacy for Young Women", "type": "workshop",
         "desc": "Learn budgeting, savings, and basics of investing.",
         "topics": ["Finance", "Empowerment"], "speaker_idx": 5},
        {"title": "Cyber Safety for Women Online", "type": "lecture",
         "desc": "How to stay safe online — social media, cyberstalking, and reporting mechanisms.",
         "topics": ["Cyber Safety", "Awareness"], "speaker_idx": 6},
        {"title": "Nutrition for Young Women", "type": "workshop",
         "desc": "Dietary guidance for energy, immunity, and overall well-being.",
         "topics": ["Nutrition", "Health"], "speaker_idx": 7},
        {"title": "Self-Defense Training Camp", "type": "camp",
         "desc": "Basic self-defense techniques workshop conducted by certified trainers.",
         "topics": ["Self-Defense", "Safety"], "speaker_idx": -1},
        {"title": "International Women's Day Celebration", "type": "celebration",
         "desc": "Cultural program, panel discussion, and awards recognizing women achievers.",
         "topics": ["Celebration", "Empowerment"], "speaker_idx": 3},
        {"title": "Menstrual Hygiene Day Awareness", "type": "workshop",
         "desc": "Open talk and Q&A on menstrual health and breaking stigma.",
         "topics": ["Health", "Hygiene"], "speaker_idx": 0},
        {"title": "Skill Development: Resume Building", "type": "workshop",
         "desc": "Practical session on crafting resumes and interview prep.",
         "topics": ["Skills", "Career"], "speaker_idx": 5},
        {"title": "Women Entrepreneurs Panel", "type": "panel",
         "desc": "Panel of women founders sharing their startup journeys.",
         "topics": ["Entrepreneurship", "Career"], "speaker_idx": 5},
        {"title": "Stress Management & Mindfulness", "type": "session",
         "desc": "Guided meditation and breathing exercises for daily stress relief.",
         "topics": ["Mental Health", "Wellness"], "speaker_idx": 2},
        {"title": "Workplace Harassment Awareness", "type": "lecture",
         "desc": "Understanding POSH Act and Internal Complaints Committee.",
         "topics": ["Law", "Workplace"], "speaker_idx": 1},
    ]

    event_ids = []
    for i, t in enumerate(event_templates):
        # spread events: some past, some upcoming
        offset = (i - 5) * 3  # -15..+30 days approx
        date = (today + timedelta(days=offset)).isoformat()
        status = "completed" if offset < 0 else ("published" if offset > 0 else "published")
        doc = {
            "title": t["title"],
            "short_description": t["desc"][:80],
            "description": t["desc"],
            "event_type": t["type"],
            "women_date_id": None,
            "date": date,
            "start_time": "10:00",
            "end_time": "12:00",
            "timezone": "Asia/Kolkata",
            "venue": random.choice(["Seminar Hall A", "Auditorium", "Room 201", "Open Quad"]),
            "capacity": random.choice([40, 50, 60, 80, 100]),
            "registration_deadline": date,
            "speaker_id": speaker_ids[t["speaker_idx"]] if t["speaker_idx"] >= 0 else None,
            "topics": t["topics"],
            "target_departments": [],  # empty = all departments
            "target_classes": [],
            "status": status,
            "registration_enabled": status == "published",
            "cover_image_url": None,
            "created_by": admin["id"],
        }
        ev = db.insert("events", doc)
        event_ids.append(ev["id"])

    # ---------- Registrations ----------
    # For each published event, register 10-25 random students
    for eid in event_ids:
        e = db.get("events", eid)
        if not e or e.get("status") != "published":
            continue
        cap = e.get("capacity") or 50
        n_regs = min(cap, random.randint(10, 25))
        for sid in random.sample(student_ids, n_regs):
            db.insert("registrations", {
                "event_id": eid,
                "student_id": sid,
                "status": "registered",
            })

    # ---------- Attendance for completed events ----------
    for eid in event_ids:
        e = db.get("events", eid)
        if not e or e.get("status") != "completed":
            continue
        regs = db.list("registrations", where={"event_id": eid, "status": "registered"})
        for r in regs:
            db.insert("attendance", {
                "event_id": eid,
                "student_id": r["student_id"],
                "status": random.choices(["present", "absent", "late"], weights=[80, 15, 5])[0],
            })

    # ---------- Sample notification ----------
    db.insert("notifications", {
        "user_id": "all",
        "title": "Welcome to WDC App!",
        "body": "Explore upcoming Women Development Cell events and register today.",
        "channel": "in_app",
        "read": False,
    })

    print(f"[WDC Seed] Done: 1 super admin, {student_count} students, {len(speakers)} speakers, "
          f"{len(event_templates)} events, {len(women_dates)} women dates.")
    print(f"[WDC Seed] Admin login: admin@wdc.edu / {settings.default_super_admin_password}")
    print(f"[WDC Seed] Sample student login: student01@wdc.edu / Student@123")


if __name__ == "__main__":
    run_seed()
