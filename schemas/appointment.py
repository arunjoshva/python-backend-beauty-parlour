from datetime import date, time

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class AppointmentCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=150)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=7, max_length=20)

    service_id: int = Field(gt=0)

    appointment_date: date
    appointment_time: time

    notes: str | None = None


# Customer information included in appointment responses.
class AppointmentCustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str


# Service information included in appointment responses.
class AppointmentServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    duration: int
    category: str


# Complete appointment response.
class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    customer_id: int
    service_id: int

    appointment_date: date
    appointment_time: time

    status: str
    notes: str | None

    customer: AppointmentCustomerResponse
    service: AppointmentServiceResponse