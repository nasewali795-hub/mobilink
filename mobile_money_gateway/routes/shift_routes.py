from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from mobile_money_gateway.database import get_db
from mobile_money_gateway.schemas.schemas import ShiftCreate, ShiftResponse, ShiftClose
from mobile_money_gateway.models.models import User, Booth, Shift, ShiftStatus, Transaction, TransactionType, TransactionStatus, UserRole
from mobile_money_gateway.routes.auth_routes import get_current_user, require_role
from mobile_money_gateway.services.transaction_service import TransactionService

router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.post("/start", response_model=ShiftResponse)
def start_shift(
    shift_data: ShiftCreate,
    booth_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only operators can start shifts")

    booth = db.query(Booth).filter(Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booth not found")

    existing_open = db.query(Shift).filter(
        Shift.operator_id == current_user.id,
        Shift.status == ShiftStatus.OPEN,
    ).first()
    if existing_open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operator already has an open shift")

    shift = Shift(
        operator_id=current_user.id,
        booth_id=booth.id,
        starting_cash=shift_data.starting_cash,
        status=ShiftStatus.OPEN,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return ShiftResponse.model_validate(shift)


@router.post("/{shift_id}/close", response_model=ShiftResponse)
def close_shift(
    shift_id: str,
    close_data: ShiftClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    if shift.operator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if shift.status == ShiftStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shift already closed")

    transactions = db.query(Transaction).filter(Transaction.shift_id == shift.id).all()
    cash_in_total = sum(t.amount for t in transactions if t.transaction_type == TransactionType.CASH_IN and t.status == TransactionStatus.SUCCESS)
    cash_out_total = sum(t.amount for t in transactions if t.transaction_type == TransactionType.CASH_OUT and t.status == TransactionStatus.SUCCESS)

    expected_closing = shift.starting_cash + cash_in_total - cash_out_total
    discrepancy = close_data.actual_cash - expected_closing

    shift.end_time = datetime.utcnow()
    shift.ending_cash = close_data.actual_cash
    shift.status = ShiftStatus.CLOSED
    shift.discrepancy = discrepancy
    shift.expected_closing_cash = expected_closing

    db.commit()
    db.refresh(shift)

    return ShiftResponse.model_validate(shift)


@router.get("/operator/me", response_model=list[ShiftResponse])
def get_my_shifts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shifts = db.query(Shift).filter(Shift.operator_id == current_user.id).order_by(Shift.start_time.desc()).all()
    return [ShiftResponse.model_validate(s) for s in shifts]


@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(
    shift_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    if shift.operator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return ShiftResponse.model_validate(shift)
