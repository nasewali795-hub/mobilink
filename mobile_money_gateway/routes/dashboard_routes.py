from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from mobile_money_gateway.database import get_db
from mobile_money_gateway.models.models import SIMCard, Transaction, Shift
from mobile_money_gateway.routes.auth_routes import require_role

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", dependencies=[Depends(require_role("admin"))])
def get_dashboard_summary(db: Session = Depends(get_db)):
    sim_cards = db.query(SIMCard).all()
    
    sim_status = [{
        "network": sim.network_name,
        "phone": sim.phone_number,
        "balance": float(sim.current_float_balance),
        "status": sim.status.value
    } for sim in sim_cards]
    
    # Get today's transactions
    today = datetime.utcnow().date()
    # Simple count for today (SQLite datetime comparison can be tricky, using basic count for demo)
    total_transactions = db.query(Transaction).count()
    
    return {
        "total_transactions": total_transactions,
        "sim_health": sim_status,
        "active_shifts": db.query(Shift).filter(Shift.status == "open").count(),
    }
