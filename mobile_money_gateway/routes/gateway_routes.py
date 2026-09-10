from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import asyncio
import random
import time
from mobile_money_gateway.database import get_db
from mobile_money_gateway.schemas.schemas import SMSWebhookPayload
from mobile_money_gateway.models.models import User, SIMCard, Transaction, TransactionStatus
from mobile_money_gateway.services.transaction_service import TransactionService
from mobile_money_gateway.services.websocket_manager import manager
from mobile_money_gateway.utils.sms_parser import SMSParser
from mobile_money_gateway.routes.auth_routes import get_current_user
from mobile_money_gateway.config import settings

router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.websocket("/ws/connect/{gateway_id}")
async def gateway_connect(websocket: WebSocket, gateway_id: str):
    await manager.connect_gateway(websocket, gateway_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "heartbeat":
                await manager.send_to_gateway(gateway_id, {"type": "heartbeat_ack"})
    except WebSocketDisconnect:
        manager.disconnect_gateway(gateway_id)


@router.websocket("/ws/tablet/{booth_id}")
async def tablet_connect(websocket: WebSocket, booth_id: str):
    await manager.connect_tablet(websocket, booth_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await manager.send_to_tablet(booth_id, {"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect_tablet(booth_id)


@router.post("/sms/inbound")
async def inbound_sms(payload: SMSWebhookPayload, db: Session = Depends(get_db)):
    parsed = SMSParser.parse(payload.message, payload.sender)
    transaction = None
    if parsed.transaction_id:
        transaction = db.query(Transaction).filter(Transaction.mno_reference_code == parsed.transaction_id).first()
    if not transaction and parsed.amount:
        transaction = db.query(Transaction).filter(
            Transaction.amount == parsed.amount,
            Transaction.status == TransactionStatus.PROCESSING,
        ).order_by(Transaction.created_at.desc()).first()

    if not transaction:
        return {"message": "No matching transaction found", "parsed": parsed.__dict__}

    service = TransactionService(db)
    if parsed.status == "failed":
        service.fail_transaction(transaction.id, parsed.error_message or "Transaction failed", parsed.raw_message)
    elif parsed.status == "success":
        service.update_status(
            transaction.id,
            TransactionStatus.SUCCESS,
            mno_ref=parsed.reference or parsed.transaction_id,
            raw_sms=parsed.raw_message,
        )
    else:
        service.flag_for_review(transaction.id, parsed.raw_message)

    await manager.send_to_tablet(transaction.booth_id, {
        "type": "transaction_update",
        "transaction_id": transaction.id,
        "status": transaction.status.value,
    })

    return {"message": "Processed", "transaction_id": transaction.id}


@router.post("/simulate/transaction/{transaction_id}")
async def simulate_transaction(transaction_id: str, db: Session = Depends(get_db)):
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if transaction.status not in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction not in simurable state")

    async def _simulate():
        await asyncio.sleep(settings.SIMULATION_DELAY_SECONDS)
        
        await manager.send_to_tablet(transaction.booth_id, {
            "type": "transaction_update",
            "transaction_id": transaction_id,
            "status": "executing_ussd",
            "detail": "Simulating USSD...",
        })
        
        await asyncio.sleep(settings.SIMULATION_DELAY_SECONDS)
        
        success = random.random() < settings.SIMULATION_SUCCESS_RATE
        
        if success:
            mno_ref = f"SIM{random.randint(100000, 999999)}"
            service.update_status(
                transaction_id,
                TransactionStatus.SUCCESS,
                mno_ref=mno_ref,
                raw_sms=f"Simulated SMS: Transaction {mno_ref} of {transaction.amount} completed.",
            )
            await manager.send_to_tablet(transaction.booth_id, {
                "type": "transaction_update",
                "transaction_id": transaction_id,
                "status": "success",
                "detail": mno_ref,
            })
        else:
            service.fail_transaction(transaction_id, "Simulated failure: insufficient balance", "Simulated SMS: Transaction failed.")
            await manager.send_to_tablet(transaction.booth_id, {
                "type": "transaction_update",
                "transaction_id": transaction_id,
                "status": "failed",
                "detail": "Insufficient customer balance",
            })

    asyncio.create_task(_simulate())
    return {"message": "Simulation started", "transaction_id": transaction_id}


@router.get("/simulate/pending")
async def get_pending_simulatable(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(
        Transaction.status.in_([TransactionStatus.PENDING, TransactionStatus.PROCESSING])
    ).all()
    return [
        {
            "id": t.id,
            "status": t.status.value,
            "amount": float(t.amount),
            "customer_phone": t.customer_phone,
            "created_at": t.created_at.isoformat(),
        }
        for t in transactions
    ]

