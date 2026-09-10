from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from mobile_money_gateway.database import get_db
from mobile_money_gateway.schemas.schemas import TransactionCreate, TransactionResponse, TransactionType, TransactionStatus
from mobile_money_gateway.models.models import User, Booth, Shift, ShiftStatus, UserRole
from mobile_money_gateway.services.transaction_service import TransactionService
from mobile_money_gateway.routes.auth_routes import get_current_user, require_role
from mobile_money_gateway.services.websocket_manager import manager

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only operators can create transactions")

    active_shift = db.query(Shift).filter(
        Shift.operator_id == current_user.id,
        Shift.status == ShiftStatus.OPEN,
    ).first()
    if not active_shift:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active shift. Start a shift first.")

    booth = db.query(Booth).filter(Booth.id == active_shift.booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booth not found")

    service = TransactionService(db)
    try:
        transaction = service.create_transaction(
            transaction_data=transaction_data,
            booth_id=booth.id,
            operator_id=current_user.id,
            shift_id=active_shift.id,
        )
        return TransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/deposit", response_model=TransactionResponse)
def deposit(transaction_data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    transaction_data.transaction_type = TransactionType.CASH_IN
    return create_transaction(transaction_data, db, current_user)

@router.post("/withdraw", response_model=TransactionResponse)
def withdraw(transaction_data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    transaction_data.transaction_type = TransactionType.CASH_OUT
    return create_transaction(transaction_data, db, current_user)

@router.post("/balance", response_model=TransactionResponse)
def balance(transaction_data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    transaction_data.transaction_type = TransactionType.BALANCE
    # For balance check, we might not need a customer phone or amount, but we keep the schema for simplicity
    return create_transaction(transaction_data, db, current_user)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if current_user.role != UserRole.ADMIN and transaction.operator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return TransactionResponse.model_validate(transaction)


@router.get("/shift/{shift_id}", response_model=list[TransactionResponse])
def get_shift_transactions(
    shift_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    if current_user.role != "admin" and shift.operator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    service = TransactionService(db)
    transactions = service.get_shift_transactions(shift_id)
    return [TransactionResponse.model_validate(t) for t in transactions]


@router.post("/{transaction_id}/cancel")
def cancel_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if transaction.status not in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction cannot be cancelled")
    if current_user.role != UserRole.ADMIN and transaction.operator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    service.fail_transaction(transaction_id, "Cancelled by operator")
    return {"message": "Transaction cancelled"}
