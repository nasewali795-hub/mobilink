from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
import asyncio
from mobile_money_gateway.models.models import Transaction, SIMCard, Shift, TransactionType, TransactionStatus
from mobile_money_gateway.services.queue_engine import queue_engine
from mobile_money_gateway.config import settings


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_fee(self, amount: Decimal, transaction_type: TransactionType) -> Decimal:
        if transaction_type == TransactionType.BALANCE:
            return Decimal("0.00")
        fee = amount * (Decimal(str(settings.DEFAULT_FEE_PERCENTAGE)) / Decimal("100"))
        fee = max(fee, Decimal(str(settings.MIN_FEE)))
        return round(fee, 2)

    def create_transaction(self, transaction_data, booth_id: str, operator_id: str, shift_id: Optional[str] = None) -> Transaction:
        fee = self.calculate_fee(transaction_data.amount, transaction_data.transaction_type)
        sim_card_id = transaction_data.sim_card_id or self._select_best_sim(transaction_data.transaction_type)

        if not sim_card_id:
            raise ValueError("No SIM card available")

        sim_card = self.db.query(SIMCard).filter(SIMCard.id == sim_card_id).first()
        if not sim_card:
            raise ValueError("SIM card not found")

        required_balance = transaction_data.amount + fee if transaction_data.transaction_type == TransactionType.CASH_IN else fee
        if sim_card.current_float_balance < required_balance:
            raise ValueError(f"Insufficient float balance on {sim_card.network_name}")

        transaction = Transaction(
            booth_id=booth_id,
            operator_id=operator_id,
            sim_card_id=sim_card_id,
            shift_id=shift_id,
            transaction_type=transaction_data.transaction_type,
            customer_phone=transaction_data.customer_phone,
            amount=transaction_data.amount,
            fee=fee,
            status=TransactionStatus.PENDING,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        network_name = sim_card.network_name
        queue_position = asyncio.run(queue_engine.enqueue_transaction(
            sim_card_id, transaction.id, network_name
        ))

        transaction.status = TransactionStatus.PROCESSING
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def _select_best_sim(self, transaction_type: TransactionType) -> Optional[str]:
        sim_cards = self.db.query(SIMCard).filter(
            SIMCard.status == SIMStatus.ONLINE
        ).order_by(SIMCard.current_float_balance.desc()).all()

        if transaction_type == TransactionType.CASH_IN:
            eligible = [s for s in sim_cards if s.current_float_balance >= 0]
        else:
            eligible = sim_cards

        if not eligible:
            return None
        return eligible[0].id

    def update_status(self, transaction_id: str, status: TransactionStatus, error_message: Optional[str] = None, mno_ref: Optional[str] = None, raw_sms: Optional[str] = None):
        transaction = self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            return None

        transaction.status = status
        if error_message:
            transaction.error_message = error_message
        if mno_ref:
            transaction.mno_reference_code = mno_ref
        if raw_sms:
            transaction.raw_sms_payload = raw_sms
        transaction.updated_at = datetime.utcnow()

        sim_card = self.db.query(SIMCard).filter(SIMCard.id == transaction.sim_card_id).first()
        if sim_card:
            if status == TransactionStatus.SUCCESS:
                if transaction.transaction_type == TransactionType.CASH_IN:
                    sim_card.current_float_balance += transaction.amount
                elif transaction.transaction_type == TransactionType.CASH_OUT:
                    sim_card.current_float_balance -= transaction.amount
                
                if transaction.transaction_type != TransactionType.BALANCE:
                    sim_card.current_float_balance -= transaction.fee

        queue_engine.mark_complete(transaction.sim_card_id)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def fail_transaction(self, transaction_id: str, error_message: str, raw_sms: Optional[str] = None):
        return self.update_status(
            transaction_id,
            TransactionStatus.FAILED,
            error_message=error_message,
            raw_sms=raw_sms,
        )

    def flag_for_review(self, transaction_id: str, raw_sms: str):
        return self.update_status(
            transaction_id,
            TransactionStatus.REQUIRES_MANUAL_REVIEW,
            error_message="SMS parsing failed - manual review required",
            raw_sms=raw_sms,
        )

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()

    def get_operator_transactions(self, operator_id: str, shift_id: Optional[str] = None):
        query = self.db.query(Transaction).filter(Transaction.operator_id == operator_id)
        if shift_id:
            query = query.filter(Transaction.shift_id == shift_id)
        return query.order_by(Transaction.created_at.desc()).all()

    def get_shift_transactions(self, shift_id: str):
        return self.db.query(Transaction).filter(Transaction.shift_id == shift_id).all()


from mobile_money_gateway.models.models import SIMStatus
