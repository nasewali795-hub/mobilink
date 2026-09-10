from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class BoothStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class SIMStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class TransactionType(str, Enum):
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    BALANCE = "balance"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


class ShiftStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class UserBase(BaseModel):
    username: str
    role: UserRole = UserRole.OPERATOR
    status: UserStatus = UserStatus.ACTIVE


class UserCreate(UserBase):
    pin: str


class UserLogin(BaseModel):
    username: str
    pin: str


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SIMCardBase(BaseModel):
    network_name: str
    phone_number: str
    slot_index: str
    current_float_balance: Decimal = 0


class SIMCardCreate(SIMCardBase):
    pass


class SIMCardResponse(SIMCardBase):
    id: str
    status: SIMStatus

    class Config:
        from_attributes = True


class BoothBase(BaseModel):
    name: str
    location: Optional[str] = None


class BoothCreate(BoothBase):
    pass


class BoothResponse(BoothBase):
    id: str
    status: BoothStatus
    suspend_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShiftBase(BaseModel):
    starting_cash: Decimal


class ShiftCreate(ShiftBase):
    pass


class ShiftResponse(ShiftBase):
    id: str
    operator_id: str
    booth_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    expected_closing_cash: Optional[Decimal] = None
    discrepancy: Optional[Decimal] = None
    status: ShiftStatus

    class Config:
        from_attributes = True


class ShiftClose(BaseModel):
    actual_cash: Decimal


class TransactionBase(BaseModel):
    transaction_type: TransactionType
    customer_phone: str = Field(..., min_length=10, max_length=15)
    amount: Decimal = Field(..., gt=0, le=50000)


class TransactionCreate(TransactionBase):
    sim_card_id: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: str
    booth_id: str
    operator_id: str
    sim_card_id: Optional[str] = None
    shift_id: Optional[str] = None
    fee: Decimal
    mno_reference_code: Optional[str] = None
    status: TransactionStatus
    error_message: Optional[str] = None
    raw_sms_payload: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SMSWebhookPayload(BaseModel):
    sender: str
    message: str
    received_at: Optional[str] = None


class GatewayHeartbeat(BaseModel):
    slot_index: str
    status: str


class QueueStatusResponse(BaseModel):
    sim_card_id: str
    network_name: str
    queue_length: int
    current_position: Optional[int] = None
    status: str
