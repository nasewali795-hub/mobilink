from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from mobile_money_gateway.models.models import SIMCard, FloatAdjustment


class FloatTracker:
    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, sim_card_id: str) -> Optional[Decimal]:
        sim = self.db.query(SIMCard).filter(SIMCard.id == sim_card_id).first()
        return sim.current_float_balance if sim else None

    def adjust_float(self, sim_card_id: str, amount: Decimal, adjustment_type: str, reference: Optional[str] = None, performed_by: Optional[str] = None):
        sim = self.db.query(SIMCard).filter(SIMCard.id == sim_card_id).first()
        if not sim:
            raise ValueError("SIM card not found")

        sim.current_float_balance += amount
        adjustment = FloatAdjustment(
            sim_card_id=sim_card_id,
            amount=amount,
            adjustment_type=adjustment_type,
            reference=reference,
            performed_by=performed_by,
        )
        self.db.add(adjustment)
        self.db.commit()
        return sim.current_float_balance

    def get_all_balances(self) -> List[dict]:
        sims = self.db.query(SIMCard).all()
        return [
            {
                "id": s.id,
                "network_name": s.network_name,
                "phone_number": s.phone_number,
                "slot_index": s.slot_index,
                "current_float_balance": float(s.current_float_balance),
                "status": s.status.value,
            }
            for s in sims
        ]

    def get_adjustment_history(self, sim_card_id: str, limit: int = 50):
        return self.db.query(FloatAdjustment).filter(
            FloatAdjustment.sim_card_id == sim_card_id
        ).order_by(FloatAdjustment.created_at.desc()).limit(limit).all()
