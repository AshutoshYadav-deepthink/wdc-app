"""
WDC App — Authentication dependency
Reads JWT from Authorization header or 'token' cookie, returns current user dict.
"""
from fastapi import Depends, HTTPException, Request, status
from typing import Optional, Dict, Any

from .security import decode_access_token
from .services import db


def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    cookie = request.cookies.get("token")
    if cookie:
        return cookie
    return None


def get_current_user(request: Request) -> Dict[str, Any]:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get("users", payload["sub"])
    if not user or not user.get("active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_role(*roles):
    """FastAPI dependency that requires any of the given roles."""
    def dep(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return dep


def require_permission(permission: str):
    """FastAPI dependency that requires a specific permission."""
    from .services import user_has_permission
    def dep(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if not user_has_permission(user.get("role", "Student"), permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
        return user
    return dep
