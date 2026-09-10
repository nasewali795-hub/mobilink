import sys
import os

# Add the parent directory to the path so we can import mobile_money_gateway
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mobile_money_gateway.database import get_db, Base, engine
from mobile_money_gateway.models.models import User, Booth, Shift, ShiftStatus, UserRole, UserStatus, BoothStatus, TransactionStatus, SIMCard, SIMStatus
from mobile_money_gateway.schemas.schemas import TransactionCreate, TransactionType
from mobile_money_gateway.services.transaction_service import TransactionService
from mobile_money_gateway.utils.sms_parser import SMSParser
from unittest.mock import patch
import asyncio

# Create a clean database for testing
Base.metadata.create_all(bind=engine)

def test_e2e_flow():
    db = next(get_db())

    # 1. Setup Data
    db.query(SIMCard).delete()
    db.query(User).delete()
    db.query(Shift).delete()
    db.query(Booth).delete()
    db.commit()

    booth = Booth(id="test_booth_1", name="Test Booth", location="Lusaka", status=BoothStatus.ACTIVE)
    operator = User(id="op_1", username="operator1", password_hash="hash", pin_hash="1234", role=UserRole.OPERATOR, status=UserStatus.ACTIVE)
    sim = SIMCard(
        id="sim_1", 
        phone_number="0966000000", 
        network_name="MTN", 
        current_float_balance=10000.0, 
        status=SIMStatus.ONLINE, 
        slot_index="1"
    )
    db.add(booth)
    db.add(operator)
    db.add(sim)
    db.commit()

    shift = Shift(id="shift_1", booth_id=booth.id, operator_id=operator.id, status=ShiftStatus.OPEN, starting_cash=0.0)
    db.add(shift)
    db.commit()

    print("[OK] Seeded test database with booth, operator, and shift.")

    # 2. Create a Transaction (Operator initiates a Withdrawal)
    tx_data = TransactionCreate(
        amount=500,
        customer_phone="0966123456",
        network="MTN",
        transaction_type=TransactionType.CASH_OUT
    )

    service = TransactionService(db)
    # Mock the Celery queue engine to avoid requiring Redis
    with patch('mobile_money_gateway.services.transaction_service.queue_engine') as mock_queue:
        async def dummy_enqueue(*args):
            return 1
        mock_queue.enqueue_transaction.side_effect = dummy_enqueue

        tx = service.create_transaction(
            transaction_data=tx_data,
            booth_id=booth.id,
            operator_id=operator.id,
            shift_id=shift.id
        )
    
    print(f"[OK] Created PENDING withdrawal transaction: {tx.id}")

    # 3. Simulate SMS from MTN (Customer completed USSD)
    mtn_sms = "Y'ello, you have received K500 from John Doe. Txn ID: 1234567890. Available balance K1500.00."
    
    parsed = SMSParser.parse(mtn_sms, "MTN Money")
    
    if parsed.status == "success":
        service.update_status(
            tx.id,
            TransactionStatus.SUCCESS,
            mno_ref=parsed.reference or parsed.transaction_id,
            raw_sms=parsed.raw_message,
        )
    
    print("[OK] Simulated incoming MTN SMS parsed and status updated.")

    # 4. Verify Transaction Status is SUCCESS
    tx_check = service.get_transaction(tx.id)
    assert tx_check.status == TransactionStatus.SUCCESS, "Transaction did not transition to SUCCESS"
    assert tx_check.mno_reference_code == "1234567890", "MNO Reference Code not extracted"

    print("[OK] End-to-End Flow Verified! Transaction is SUCCESS and MNO ref is saved.")

if __name__ == "__main__":
    test_e2e_flow()
