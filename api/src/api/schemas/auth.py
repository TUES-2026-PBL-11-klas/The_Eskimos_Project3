"""Pydantic schemas for auth endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str
    expires_at: datetime


class SessionSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    created_at: datetime
    expires_at: datetime
    user_agent: str | None


class UserSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    display_name: str | None
    created_at: datetime
