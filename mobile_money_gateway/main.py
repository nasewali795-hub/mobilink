from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from mobile_money_gateway.config import settings
from mobile_money_gateway.database import engine, Base
from mobile_money_gateway.models.models import User, SIMCard, Booth, Shift, Transaction, FloatAdjustment
from mobile_money_gateway.routes import auth_routes, transaction_routes, sim_routes, booth_routes, shift_routes, admin_routes, gateway_routes, dashboard_routes
from mobile_money_gateway.state import seed_initial_data

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Booth Central-SIM Mobile Money Gateway",
    description="Centralized SIM gateway for multi-booth mobile money transactions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(transaction_routes.router)
app.include_router(sim_routes.router)
app.include_router(booth_routes.router)
app.include_router(shift_routes.router)
app.include_router(admin_routes.router)
app.include_router(gateway_routes.router)
app.include_router(dashboard_routes.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mobile-money-gateway"}


@app.on_event("startup")
def on_startup():
    seed_initial_data()
