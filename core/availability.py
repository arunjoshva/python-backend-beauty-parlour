from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("Asia/Kolkata")

# Python weekday: Monday = 0, Sunday = 6
WORKING_DAYS = {0, 1, 2, 3, 4, 5}

OPENING_TIME = time(9, 0)
CLOSING_TIME = time(19, 0)

BREAK_START = time(13, 0)
BREAK_END = time(14, 0)

SLOT_INTERVAL_MINUTES = 15


def is_working_day(appointment_date: date) -> bool:
    return appointment_date.weekday() in WORKING_DAYS


def is_within_working_hours(
    appointment_time: time,
    duration: int,
) -> bool:

    start = datetime.combine(date.today(), appointment_time)
    end = start + timedelta(minutes=duration)

    opening = datetime.combine(date.today(), OPENING_TIME)
    closing = datetime.combine(date.today(), CLOSING_TIME)

    if start < opening or end > closing:
        return False

    break_start = datetime.combine(date.today(), BREAK_START)
    break_end = datetime.combine(date.today(), BREAK_END)

    # Check whether the appointment overlaps the break
    if start < break_end and end > break_start:
        return False

    return True


def generate_time_slots(appointment_date: date) -> list[time]:
    slots = []

    current = datetime.combine(appointment_date, OPENING_TIME)
    closing = datetime.combine(appointment_date, CLOSING_TIME)

    while current < closing:
        slots.append(current.time())
        current += timedelta(minutes=SLOT_INTERVAL_MINUTES)

    return slots