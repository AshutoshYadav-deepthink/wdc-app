"""
WDC App — Database Service Layer

This module abstracts all persistence behind one `db` object.
When USE_FIREBASE=true, it uses real Firebase Firestore.
When USE_FIREBASE=false, it uses a local JSON file (`local_db.json`)
so the app runs immediately for college demos without credentials.

Every other module imports `db` and never knows which backend is active.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import BASE_DIR, settings

# ---------------------------------------------------------------------------
# Role / permission constants (mirrors roles_permissions.json)
# ---------------------------------------------------------------------------
ROLES = ["Super Admin", "Admin", "Coordinator", "Staff", "Student"]

PERMISSION_CATALOG = [
    "VIEW_PUBLIC",
    "MANAGE_EVENTS",
    "MANAGE_SPEAKERS",
    "MANAGE_REGISTRATIONS",
    "MANAGE_ATTENDANCE",
    "SEND_NOTIFICATIONS",
    "VIEW_REPORTS",
    "MANAGE_USERS",
    "CHANGE_USER_ROLE",
    "SYSTEM_SETTINGS",
]

# Default permission matrix per role
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "Super Admin": PERMISSION_CATALOG[:],  # everything
    "Admin": [
        "VIEW_PUBLIC", "MANAGE_EVENTS", "MANAGE_SPEAKERS", "MANAGE_REGISTRATIONS",
        "MANAGE_ATTENDANCE", "SEND_NOTIFICATIONS", "VIEW_REPORTS", "MANAGE_USERS",
    ],
    "Coordinator": [
        "VIEW_PUBLIC", "MANAGE_EVENTS", "MANAGE_REGISTRATIONS", "MANAGE_ATTENDANCE",
        "SEND_NOTIFICATIONS", "VIEW_REPORTS",
    ],
    "Staff": [
        "VIEW_PUBLIC", "MANAGE_ATTENDANCE", "VIEW_REPORTS",
    ],
    "Student": ["VIEW_PUBLIC"],
}

COLLECTIONS = [
    "users", "students", "roles", "permissions", "events", "speakers",
    "women_dates", "registrations", "attendance", "notifications",
    "notification_campaigns", "audit_logs",
]

DEPARTMENTS = ["BSc IT", "BMS", "BAF", "BCom"]
CLASSES = {
    "BSc IT": ["FYBSc IT", "SYBSc IT", "TYBSc IT"],
    "BMS": ["FYBMS", "SYBMS", "TYBMS"],
    "BMS": ["FYBMS", "SYBMS", "TYBMS"],
    "BAF": ["FYBAF", "SYBAF", "TYBAF"],
    "BCom": ["FYBCom", "SYBCom", "TYBCom"],
}

REGISTRATION_STATUSES = ["registered", "cancelled", "waitlisted"]
ATTENDANCE_STATUSES = ["present", "absent", "late"]
EVENT_STATUSES = ["draft", "published", "closed", "cancelled", "completed"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


# ---------------------------------------------------------------------------
# Local JSON fallback backend
# ---------------------------------------------------------------------------
class LocalJSONDB:
    """Tiny thread-safe JSON file 'database' that mimics a Firestore collection store."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._data: Dict[str, List[Dict[str, Any]]] = {c: [] for c in COLLECTIONS}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                for c in COLLECTIONS:
                    self._data[c] = raw.get(c, [])
            except Exception:
                pass  # corrupt file -> start fresh

    def _persist(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, default=str, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # -- collection helpers --
    def list(self, collection: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with self._lock:
            rows = list(self._data.get(collection, []))
        if where:
            rows = [r for r in rows if all(r.get(k) == v for k, v in where.items())]
        return rows

    def get(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for r in self._data.get(collection, []):
                if r.get("id") == doc_id:
                    return dict(r)
        return None

    def insert(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in doc:
            doc["id"] = _new_id()
        doc.setdefault("created_at", _now_iso())
        doc.setdefault("updated_at", _now_iso())
        with self._lock:
            self._data.setdefault(collection, []).append(doc)
            self._persist()
        return doc

    def update(self, collection: str, doc_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            for r in self._data.get(collection, []):
                if r.get("id") == doc_id:
                    r.update(patch)
                    r["updated_at"] = _now_iso()
                    self._persist()
                    return dict(r)
        return None

    def delete(self, collection: str, doc_id: str) -> bool:
        with self._lock:
            rows = self._data.get(collection, [])
            for i, r in enumerate(rows):
                if r.get("id") == doc_id:
                    rows.pop(i)
                    self._persist()
                    return True
        return False

    def count(self, collection: str, where: Optional[Dict[str, Any]] = None) -> int:
        return len(self.list(collection, where))


# ---------------------------------------------------------------------------
# Firebase Firestore backend (real)
# ---------------------------------------------------------------------------
class FirebaseDB:
    """Thin wrapper around firebase_admin.firestore.client()."""

    def __init__(self):
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred_path = settings.firebase_credentials_path
        if not os.path.isabs(cred_path):
            cred_path = str(BASE_DIR / cred_path)

        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase credentials not found at {cred_path}. "
                "Set USE_FIREBASE=false or place serviceAccountKey.json there."
            )

        cred = credentials.Certificate(cred_path)
        try:
            firebase_admin.initialize_app(cred)
        except ValueError:
            # already initialized
            pass
        self._client = firestore.client()

    def _coll(self, name):
        return self._client.collection(name)

    def list(self, collection, where=None):
        q = self._coll(collection)
        if where:
            for k, v in where.items():
                q = q.where(k, "==", v)
        return [dict(d.to_dict(), id=d.id) for d in q.stream()]

    def get(self, collection, doc_id):
        d = self._coll(collection).document(doc_id).get()
        if not d.exists:
            return None
        return dict(d.to_dict(), id=d.id)

    def insert(self, collection, doc):
        if "id" not in doc:
            doc["id"] = _new_id()
        doc.setdefault("created_at", _now_iso())
        doc.setdefault("updated_at", _now_iso())
        self._coll(collection).document(doc["id"]).set(doc)
        return doc

    def update(self, collection, doc_id, patch):
        patch["updated_at"] = _now_iso()
        self._coll(collection).document(doc_id).update(patch)
        return self.get(collection, doc_id)

    def delete(self, collection, doc_id):
        self._coll(collection).document(doc_id).delete()
        return True

    def count(self, collection, where=None):
        return len(self.list(collection, where))


# ---------------------------------------------------------------------------
# Public db handle
# ---------------------------------------------------------------------------
if settings.use_firebase:
    try:
        db = FirebaseDB()
        print("[WDC] Using Firebase Firestore backend.")
    except Exception as e:
        print(f"[WDC] Firebase init failed: {e}. Falling back to local JSON.")
        db = LocalJSONDB(BASE_DIR / "local_db.json")
        print("[WDC] Using LOCAL JSON fallback backend (local_db.json).")
else:
    db = LocalJSONDB(BASE_DIR / "local_db.json")
    print("[WDC] Using LOCAL JSON backend (USE_FIREBASE=false).")


# ---------------------------------------------------------------------------
# Helper utilities used across routers
# ---------------------------------------------------------------------------
def user_has_permission(user_role: str, permission: str) -> bool:
    """Special rule: CHANGE_USER_ROLE always allowed for Super Admin."""
    if permission == "CHANGE_USER_ROLE" and user_role == "Super Admin":
        return True
    if user_role == "Student" and permission == "CHANGE_USER_ROLE":
        return False
    return permission in ROLE_PERMISSIONS.get(user_role, [])


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    rows = db.list("users", where={"email": email.lower()})
    return rows[0] if rows else None


def create_user(email: str, password_hash: str, role: str, name: str,
                department: Optional[str] = None, class_year: Optional[str] = None) -> Dict[str, Any]:
    user = {
        "email": email.lower(),
        "password_hash": password_hash,
        "role": role,
        "name": name,
        "department": department,
        "class_year": class_year,
        "active": True,
    }
    return db.insert("users", user)


def audit(actor_id: str, action: str, target: Optional[str] = None, meta: Optional[Dict] = None):
    db.insert("audit_logs", {
        "actor_id": actor_id,
        "action": action,
        "target": target,
        "meta": meta or {},
    })
