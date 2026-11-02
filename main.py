
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import services, admin, customers, appointments

load_dotenv()

app = FastAPI(
    title="Jerusha Beauty Parlour API",
    description="Backend API for appointment booking system",
    version="1.0.0",
)

# CORS configuration
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

allowed_origins = [
    origin.strip()
    for origin in cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
    ],
)

# Register API routers
app.include_router(services.router)
app.include_router(admin.router)
app.include_router(customers.router)
app.include_router(appointments.router)


@app.get("/")
def home():
    return {
        "message": "Welcome to Jerusha Beauty Parlour API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }
