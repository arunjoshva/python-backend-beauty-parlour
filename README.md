# Jerusha Beauty Parlour – Backend

The backend API for the **Jerusha Beauty Parlour Appointment Booking System**, developed using Python and FastAPI. It handles appointment bookings, customer records, service management, admin authentication, and database operations.

## Live API

**Backend URL:** https://python-backend-beauty-parlour.onrender.com/

**API Documentation:** https://python-backend-beauty-parlour.onrender.com/docs

**Frontend:** https://python-frontend-beauty-parlour.netlify.app/

## Technologies Used

- **Python 3.14** – Programming language
- **FastAPI** – Backend web framework
- **SQLAlchemy 2** – ORM
- **Alembic** – Database migrations
- **PostgreSQL** – Relational database
- **Psycopg 3** – PostgreSQL database driver
- **PyJWT** – JWT authentication
- **pwdlib with Argon2** – Password hashing
- **Render** – Backend deployment
- **Neon** – PostgreSQL database hosting

## Features

### Customer and Appointment Management

- Create and manage customer records.
- Reuse existing customer records based on email.
- Create appointment bookings.
- Retrieve available appointment time slots.
- Validate appointment dates and times.
- Prevent overlapping appointment bookings.

### Service Management

- Retrieve active services for customers.
- Create new services.
- Update existing services.
- Activate and deactivate services.
- Retrieve services for administration, including inactive services.

### Admin Management

- Admin login and logout.
- Verify authenticated admin sessions.
- Retrieve admin information.
- Protected admin API endpoints.

### Authentication and Security

- JWT-based authentication using HS256.
- JWT stored in an HttpOnly cookie.
- Password hashing using Argon2.
- CSRF protection using the double-submit cookie pattern.
- CORS configured for the frontend origin.
- Admin authorization through protected backend dependencies.

## Appointment Availability

The booking system uses the following availability schedule:

| Setting | Configuration |
|---|---|
| Time zone | Asia/Kolkata |
| Working days | Monday – Saturday |
| Working hours | 9:00 AM – 7:00 PM |
| Break time | 1:00 PM – 2:00 PM |
| Appointment slot interval(varies based on service) | 15 minutes |

## Project Structure

```text
backend/
├── core/
│   ├── security.py
│   └── dependencies.py
├── database/
│   ├── connection.py
│   └── dependencies.py
├── models/
├── routes/
│   ├── services.py
│   ├── admin.py
│   ├── customers.py
│   └── appointments.py
├── schemas/
│   ├── auth.py
│   ├── customer.py
│   └── appointment.py
├── migrations/
├── main.py
├── requirements.txt
├── alembic.ini
├── .env
└── README.md
```

## API Documentation

FastAPI automatically generates interactive API documentation.

After starting the backend, visit:

- **Swagger UI:** https://python-backend-beauty-parlour.onrender.com/docs
- **ReDoc:** https://python-backend-beauty-parlour.onrender.com/redoc

## Deployment

The backend is deployed on **Render**, and the PostgreSQL database is hosted on **Neon**.

Deployment configuration includes:

- PostgreSQL database connection.
- Environment variables configured in Render.
- Frontend origin configured through CORS.
- Secure cookies enabled for production.
- Database migrations applied using Alembic.

---

Developed as a full-stack web development portfolio project.