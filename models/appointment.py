from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.customer import Customer
    from models.service import Service

from datetime import datetime, date, time

from sqlalchemy import (
    Integer,
    String,
    Text,
    Date,
    Time,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
    )

    service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("services.id"),
        nullable=False,
    )

    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
    )

    # Each appointment belongs to one customer.
    customer: Mapped["Customer"] = relationship(
        back_populates="appointments"
    )

    # Each appointment belongs to one service.
    service: Mapped["Service"] = relationship(
        back_populates="appointments"
    )