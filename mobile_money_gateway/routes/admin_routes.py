from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from mobile_money_gateway.database import get_db
from mobile_money_gateway.schemas.schemas import SIMCardResponse
from mobile_money_gateway.models.models import User, SIMCard, Transaction, TransactionStatus
from mobile_money_gateway.routes.auth_routes import get_current_user, require_role
from mobile_money_gateway.services.float_tracker import FloatTracker
from mobile_money_gateway.services.transaction_service import TransactionService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/balances", response_model=list[dict])
def get_all_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    tracker = FloatTracker(db)
    return tracker.get_all_balances()


@router.post("/float/adjust")
def adjust_float(
    sim_card_id: str,
    amount: Decimal,
    adjustment_type: str,
    reference: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    if adjustment_type not in ["credit", "debit", "correction", "topup"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid adjustment type")
    tracker = FloatTracker(db)
    try:
        new_balance = tracker.adjust_float(
            sim_card_id=sim_card_id,
            amount=amount,
            adjustment_type=adjustment_type,
            reference=reference,
            performed_by=current_user.username,
        )
        return {"message": "Float adjusted", "new_balance": float(new_balance)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/float/history/{sim_card_id}")
def get_float_history(
    sim_card_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    tracker = FloatTracker(db)
    history = tracker.get_adjustment_history(sim_card_id, limit)
    return [
        {
            "id": h.id,
            "amount": float(h.amount),
            "adjustment_type": h.adjustment_type,
            "reference": h.reference,
            "performed_by": h.performed_by,
            "created_at": h.created_at.isoformat(),
        }
        for h in history
    ]


@router.get("/transactions/pending-review")
def get_pending_review(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    from mobile_money_gateway.models.models import TransactionStatus
    transactions = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.REQUIRES_MANUAL_REVIEW
    ).order_by(Transaction.created_at.desc()).all()
    service = TransactionService(db)
    return [
        {
            "id": t.id,
            "booth_id": t.booth_id,
            "operator_id": t.operator_id,
            "amount": float(t.amount),
            "customer_phone": t.customer_phone,
            "error_message": t.error_message,
            "raw_sms_payload": t.raw_sms_payload,
            "created_at": t.created_at.isoformat(),
        }
        for t in transactions
    ]


@router.post("/transactions/{transaction_id}/resolve")
def resolve_manual_review(
    transaction_id: str,
    approved: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if transaction.status != TransactionStatus.REQUIRES_MANUAL_REVIEW:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction not pending review")
    if approved:
        service.update_status(transaction_id, TransactionStatus.SUCCESS)
    else:
        service.fail_transaction(transaction_id, "Rejected by admin")
    return {"message": "Transaction resolved"}


from mobile_money_gateway.services.admin_service import AdminService
from mobile_money_gateway.services.audit_service import AuditService
from pydantic import BaseModel

class ConfigUpdate(BaseModel):
    value: str

@router.post("/booths/{booth_id}/block")
def block_booth(booth_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AdminService(db)
    booth = service.block_booth(booth_id, current_user.id)
    if not booth:
        raise HTTPException(status_code=404, detail="Booth not found")
    return {"message": "Booth blocked successfully"}

@router.post("/booths/{booth_id}/suspend")
def suspend_booth(booth_id: str, duration_hours: int = 24, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AdminService(db)
    booth = service.suspend_booth(booth_id, current_user.id, duration_hours)
    if not booth:
        raise HTTPException(status_code=404, detail="Booth not found")
    return {"message": f"Booth suspended for {duration_hours} hours"}

@router.delete("/booths/{booth_id}")
def delete_booth(booth_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AdminService(db)
    success = service.delete_booth(booth_id, current_user.id)
    return {"message": "Booth deleted successfully"}

@router.post("/operators/{operator_id}/reset-password")
def reset_operator_password(operator_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AdminService(db)
    new_pwd = service.reset_operator_password(operator_id, current_user.id)
    if not new_pwd:
        raise HTTPException(status_code=404, detail="Operator not found")
    return {"message": "Password reset", "new_password": new_pwd}

@router.post("/operators/{operator_id}/deactivate")
def deactivate_operator(operator_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AdminService(db)
    op = service.deactivate_operator(operator_id, current_user.id)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    return {"message": "Operator deactivated"}

@router.put("/config/transaction-limits/{network}")
def update_transaction_limits(network: str, config: ConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AdminService(db)
    service.update_transaction_limits(network, config.value, current_user.id)
    return {"message": "Transaction limits updated"}

@router.put("/config/queue-priority")
def set_queue_priority(config: ConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AdminService(db)
    service.set_queue_priority(config.value, current_user.id)
    return {"message": "Queue priority rules updated"}

@router.get("/booths/{booth_id}/details")
def get_booth_details(booth_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AuditService(db)
    details = service.get_booth_details(booth_id)
    if not details:
        raise HTTPException(status_code=404, detail="Booth not found")
    return details

@router.get("/audit-logs")
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin"]))):
    service = AuditService(db)
    logs = service.get_all_audit_logs(limit)
    return logs
