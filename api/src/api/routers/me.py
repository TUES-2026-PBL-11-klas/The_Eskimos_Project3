"""User-scoped endpoints: saved events, calendar, and reminders."""

from __future__ import annotations

import calendar as calendar_module
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.deps import (
    CurrentUserDep,
    MeServiceDep,
    ReminderServiceDep,
    SavedEventServiceDep,
)
from api.domain.exceptions import AlreadySavedError, EventNotFoundError, ReminderNotFoundError
from api.schemas.me import MeSchema, MeUpdateRequest
from api.schemas.reminders import ReminderRequest, ReminderSchema
from api.schemas.saved import CalendarDaySchema, CalendarSchema, SavedEventSchema

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeSchema)
async def get_me(current_user: CurrentUserDep, service: MeServiceDep) -> MeSchema:
    return await service.get_me(current_user)


@router.patch("", response_model=MeSchema)
async def update_me(
    body: MeUpdateRequest,
    current_user: CurrentUserDep,
    service: MeServiceDep,
) -> MeSchema:
    return await service.update_me(
        current_user, body.display_name, body.default_lead_hours, body.timezone
    )


def _resolve_date_range(
    month: str | None,
    from_date: date | None,
    to_date: date | None,
) -> tuple[datetime, datetime]:
    """Resolve query params into an inclusive UTC datetime window."""
    if month is not None:
        year, month_num = int(month[:4]), int(month[5:])
        _, last_day = calendar_module.monthrange(year, month_num)
        return (
            datetime(year, month_num, 1, tzinfo=UTC),
            datetime(year, month_num, last_day, 23, 59, 59, 999999, tzinfo=UTC),
        )
    if from_date is not None and to_date is not None:
        return (
            datetime(from_date.year, from_date.month, from_date.day, tzinfo=UTC),
            datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, 999999, tzinfo=UTC),
        )
    # Default: current calendar month.
    today = datetime.now(UTC)
    _, last_day = calendar_module.monthrange(today.year, today.month)
    return (
        datetime(today.year, today.month, 1, tzinfo=UTC),
        datetime(today.year, today.month, last_day, 23, 59, 59, 999999, tzinfo=UTC),
    )


@router.post("/saved/{event_id}", response_model=SavedEventSchema, status_code=201)
async def save_event(
    event_id: int,
    current_user: CurrentUserDep,
    service: SavedEventServiceDep,
) -> SavedEventSchema:
    try:
        return await service.save(current_user.id, event_id)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found") from None
    except AlreadySavedError:
        raise HTTPException(status_code=409, detail="Event already saved") from None


@router.delete("/saved/{saved_id}", status_code=204)
async def unsave_event(
    saved_id: int,
    current_user: CurrentUserDep,
    service: SavedEventServiceDep,
) -> None:
    try:
        await service.unsave(current_user.id, saved_id)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Saved event not found") from None


@router.get("/saved", response_model=list[SavedEventSchema])
async def list_saved(
    current_user: CurrentUserDep,
    service: SavedEventServiceDep,
) -> list[SavedEventSchema]:
    return await service.list_saved(current_user.id)


@router.get("/calendar", response_model=CalendarSchema)
async def get_calendar(
    current_user: CurrentUserDep,
    service: SavedEventServiceDep,
    month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> CalendarSchema:
    from_dt, to_dt = _resolve_date_range(month, from_date, to_date)
    grouped = await service.calendar(current_user.id, from_dt, to_dt)
    return CalendarSchema(
        days=[CalendarDaySchema(date=day, events=ses) for day, ses in grouped.items()]
    )


# ── Reminders — /reminders/due MUST come before /reminders/{reminder_id} ─────

@router.post("/saved/{saved_id}/reminder", response_model=ReminderSchema, status_code=201)
async def create_reminder(
    saved_id: int,
    req: ReminderRequest,
    current_user: CurrentUserDep,
    service: ReminderServiceDep,
) -> ReminderSchema:
    try:
        return await service.create(
            current_user.id, saved_id, req.lead_hours, req.remind_at
        )
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Saved event not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/reminders/due", response_model=list[ReminderSchema])
async def list_due_reminders(
    current_user: CurrentUserDep,
    service: ReminderServiceDep,
) -> list[ReminderSchema]:
    return await service.list_due(current_user.id)


@router.get("/reminders", response_model=list[ReminderSchema])
async def list_reminders(
    current_user: CurrentUserDep,
    service: ReminderServiceDep,
) -> list[ReminderSchema]:
    return await service.list_for_user(current_user.id)


@router.delete("/reminders/{reminder_id}", status_code=204)
async def cancel_reminder(
    reminder_id: int,
    current_user: CurrentUserDep,
    service: ReminderServiceDep,
) -> None:
    try:
        await service.cancel(current_user.id, reminder_id)
    except ReminderNotFoundError:
        raise HTTPException(status_code=404, detail="Reminder not found") from None
