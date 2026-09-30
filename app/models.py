"""ORM models. Minimal v1 schema: a household and the plans generated for it."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    size: Mapped[int] = mapped_column(Integer, default=2)
    store_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    diet: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    plans: Mapped[list["Plan"]] = relationship(back_populates="household")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int | None] = mapped_column(
        ForeignKey("households.id"), nullable=True
    )
    week: Mapped[str] = mapped_column(String(12))
    # The generated plan (meals + consolidated shopping list) as JSON.
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    household: Mapped[Household | None] = relationship(back_populates="plans")


class RecipeSteps(Base):
    """Claude-generated cooking steps, cached once per recipe."""

    __tablename__ = "recipe_steps"

    recipe_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    steps: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
