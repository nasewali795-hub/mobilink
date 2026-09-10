from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from mobile_money_gateway.models.models import Booth, Transaction, BoothAuditLog, TransactionLog, AdminActionLog, User

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def get_booth_details(self, booth_id: str):
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if not booth:
            return None

        transactions = self.db.query(Transaction).filter(Transaction.booth_id == booth_id).order_by(Transaction.created_at.desc()).limit(50).all()
        audit_trail = self.db.query(BoothAuditLog).filter(BoothAuditLog.booth_id == booth_id).order_by(BoothAuditLog.timestamp.desc()).limit(50).all()
        
        return {
            "booth_data": booth,
            "transactions": transactions,
            "audit_trail": audit_trail
        }

    def log_booth_action(self, booth_id: str, action_type: str, performed_by: str):
        log = BoothAuditLog(
            booth_id=booth_id,
            action_type=action_type,
            performed_by=performed_by
        )
        self.db.add(log)
        self.db.commit()

    def log_transaction_event(self, tx_id: str, booth_id: str, event_type: str):
        log = TransactionLog(
            transaction_id=tx_id,
            booth_id=booth_id,
            event_type=event_type
        )
        self.db.add(log)
        self.db.commit()

    def get_all_audit_logs(self, limit: int = 100):
        return self.db.query(AdminActionLog).order_by(AdminActionLog.timestamp.desc()).limit(limit).all()
