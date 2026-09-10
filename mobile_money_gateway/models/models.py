from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql.sqltypes import DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import datetime
import enum

from mobile_money_gateway.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class BoothStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class SIMStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class TransactionType(str, enum.Enum):
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    BALANCE = "balance"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


class ShiftStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    pin_hash = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OPERATOR)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    shifts = relationship("Shift", back_populates="operator")
    transactions = relationship("Transaction", back_populates="operator")


class SIMCard(Base):
    __tablename__ = "sim_cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    slot_index = Column(String, nullable=False)
    current_float_balance = Column(DECIMAL, nullable=False, default=0)
    status = Column(Enum(SIMStatus), nullable=False, default=SIMStatus.OFFLINE)

    transactions = relationship("Transaction", back_populates="sim_card")


class Booth(Base):
    __tablename__ = "booths"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    location = Column(String)
    status = Column(Enum(BoothStatus), nullable=False, default=BoothStatus.ACTIVE)
    suspend_until = Column(DateTime, nullable=True)

    shifts = relationship("Shift", back_populates="booth")
    transactions = relationship("Transaction", back_populates="booth")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operator_id = Column(String, ForeignKey("users.id"), nullable=False)
    booth_id = Column(String, ForeignKey("booths.id"), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    starting_cash = Column(DECIMAL, nullable=False)
    ending_cash = Column(DECIMAL, nullable=True)
    expected_closing_cash = Column(DECIMAL, nullable=True)
    discrepancy = Column(DECIMAL, nullable=True)
    status = Column(Enum(ShiftStatus), nullable=False, default=ShiftStatus.OPEN)

    operator = relationship("User", back_populates="shifts")
    booth = relationship("Booth", back_populates="shifts")
    transactions = relationship("Transaction", back_populates="shift")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booth_id = Column(String, ForeignKey("booths.id"), nullable=False)
    operator_id = Column(String, ForeignKey("users.id"), nullable=False)
    sim_card_id = Column(String, ForeignKey("sim_cards.id"), nullable=False)
    shift_id = Column(String, ForeignKey("shifts.id"), nullable=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    customer_phone = Column(String, nullable=False)
    amount = Column(DECIMAL, nullable=False)
    fee = Column(DECIMAL, nullable=False, default=0)
    mno_reference_code = Column(String, nullable=True)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    error_message = Column(String, nullable=True)
    raw_sms_payload = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    booth = relationship("Booth", back_populates="transactions")
    operator = relationship("User", back_populates="transactions")
    sim_card = relationship("SIMCard", back_populates="transactions")
    shift = relationship("Shift", back_populates="transactions")


class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class BoothAuditLog(Base):
    __tablename__ = "booth_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booth_id = Column(String, ForeignKey("booths.id"), nullable=False)
    action_type = Column(String, nullable=False)
    performed_by = Column(String, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class TransactionLog(Base):
    __tablename__ = "transaction_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    booth_id = Column(String, ForeignKey("booths.id"), nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = Column(String, ForeignKey("users.id"), nullable=False)
    target_booth = Column(String, ForeignKey("booths.id"), nullable=True)
    action_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class FloatAdjustment(Base):
    __tablename__ = "float_adjustments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sim_card_id = Column(String, ForeignKey("sim_cards.id"), nullable=False)
    amount = Column(DECIMAL, nullable=False)
    adjustment_type = Column(String, nullable=False)
    reference = Column(String, nullable=True)
    performed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
