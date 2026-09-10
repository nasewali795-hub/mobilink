from sqlalchemy.orm import Session
from mobile_money_gateway.models.models import User, SIMCard, Booth, UserRole, SIMStatus
from mobile_money_gateway.utils.auth import hash_pin
from decimal import Decimal


def seed_initial_data(db: Session = None):
    if db is None:
        from mobile_money_gateway.database import SessionLocal
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        if db.query(User).count() == 0:
            admin = User(
                username="admin",
                pin_hash=hash_pin("admin123"),
                role=UserRole.ADMIN,
                status="active",
            )
            operator1 = User(
                username="operator1",
                pin_hash=hash_pin("1234"),
                role=UserRole.OPERATOR,
                status="active",
            )
            operator2 = User(
                username="operator2",
                pin_hash=hash_pin("1234"),
                role=UserRole.OPERATOR,
                status="active",
            )
            db.add_all([admin, operator1, operator2])

        if db.query(Booth).count() == 0:
            booth1 = Booth(name="Booth 1", location="Main Market")
            booth2 = Booth(name="Booth 2", location="Town Center")
            booth3 = Booth(name="Booth 3", location="Bus Station")
            db.add_all([booth1, booth2, booth3])

        if db.query(SIMCard).count() == 0:
            sim1 = SIMCard(
                network_name="MTN",
                phone_number="+260977000001",
                slot_index="1",
                current_float_balance=Decimal("50000.00"),
                status=SIMStatus.ONLINE,
            )
            sim2 = SIMCard(
                network_name="Airtel",
                phone_number="+260977000002",
                slot_index="2",
                current_float_balance=Decimal("50000.00"),
                status=SIMStatus.ONLINE,
            )
            db.add_all([sim1, sim2])

        db.commit()
    finally:
        if should_close:
            db.close()
