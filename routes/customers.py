from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.dependencies import get_db
from models.customer import Customer
from models.admin import Admin
from schemas.customer import CustomerCreate, CustomerResponse
from core.dependencies import get_current_admin


router = APIRouter(
    prefix="/api/customers",
    tags=["Customers"],
)


# POST: Create a customer or retrieve an existing customer
@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
)
def create_or_get_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    email = str(customer_data.email).strip().lower()

    statement = select(Customer).where(
        Customer.email == email
    )

    existing_customer = db.scalars(statement).one_or_none()

    if existing_customer:
        return existing_customer

    new_customer = Customer(
        name=customer_data.name.strip(),
        email=email,
        phone=customer_data.phone.strip(),
    )

    try:
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

    except Exception:
        db.rollback()
        raise

    return new_customer


# GET: Retrieve all customers (admin only)
@router.get(
    "/",
    response_model=list[CustomerResponse],
)
def get_customers(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    statement = select(Customer).order_by(Customer.id)

    return db.scalars(statement).all()


# GET: Retrieve one customer (admin only)
@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer