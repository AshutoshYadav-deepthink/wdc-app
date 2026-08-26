"""
WDC App — Auth Router
Student signup/login/logout + Admin login + /api/me
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from datetime import timedelta

from ..auth import get_current_user
from ..config import settings
from ..schemas import StudentSignup, StudentLogin, AdminLogin, TokenOut
from ..security import create_access_token, hash_password, verify_password
from ..services import db, create_user, find_user_by_email, audit, ROLE_PERMISSIONS

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenOut, status_code=201)
def signup(payload: StudentSignup, response: Response):
    if payload.department not in ["BSc IT", "BMS", "BAF", "BCom"]:
        raise HTTPException(400, "Invalid department")
    if find_user_by_email(payload.email):
        raise HTTPException(409, "Email already registered")
    user = create_user(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="Student",
        name=payload.full_name,
        department=payload.department,
        class_year=payload.class_year,
    )
    # also create linked student profile
    db.insert("students", {
        "user_id": user["id"],
        "name": payload.full_name,
        "email": payload.email.lower(),
        "department": payload.department,
        "class_year": payload.class_year,
    })
    token = create_access_token(user["id"], "Student", user["name"])
    response.set_cookie("token", token, httponly=True, samesite="lax")
    return TokenOut(access_token=token, role="Student", name=user["name"])


@router.post("/login", response_model=TokenOut)
def login(payload: StudentLogin, response: Response):
    user = find_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(401, "Invalid email or password")
    if user.get("role") != "Student":
        raise HTTPException(403, "Use the admin login page for staff accounts")
    if not user.get("active", True):
        raise HTTPException(403, "Account disabled")
    token = create_access_token(user["id"], user["role"], user.get("name"))
    response.set_cookie("token", token, httponly=True, samesite="lax")
    return TokenOut(access_token=token, role=user["role"], name=user.get("name"))


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"ok": True, "message": "Logged out"}


@router.post("/admin/login", response_model=TokenOut)
def admin_login(payload: AdminLogin, response: Response):
    user = find_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(401, "Invalid credentials")
    if user.get("role") == "Student":
        raise HTTPException(403, "Not an admin account")
    if not user.get("active", True):
        raise HTTPException(403, "Account disabled")
    token = create_access_token(user["id"], user["role"], user.get("name"))
    response.set_cookie("token", token, httponly=True, samesite="lax")
    audit(user["id"], "admin_login")
    return TokenOut(access_token=token, role=user["role"], name=user.get("name"))


# Convenience: current user info via /api/me
@router.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name"),
        "role": user.get("role"),
        "department": user.get("department"),
        "class_year": user.get("class_year"),
        "permissions": ROLE_PERMISSIONS.get(user.get("role", "Student"), []),
    }
