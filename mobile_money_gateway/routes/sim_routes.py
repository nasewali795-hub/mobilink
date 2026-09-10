from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from mobile_money_gateway.database import get_db
from mobile_money_gateway.schemas.schemas import SIMCardCreate, SIMCardResponse
from mobile_money_gateway.models.models import User
from mobile_money_gateway.routes.auth_routes import get_current_user, require_role
from mobile_money_gateway.services.float_tracker import FloatTracker

router = APIRouter(prefix="/sim-cards", tags=["sim-cards"])


@router.post("", response_model=SIMCardResponse)
def create_sim_card(
    sim_data: SIMCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    from mobile_money_gateway.models.models import SIMCard, SIMStatus
    existing = db.query(SIMCard).filter(SIMCard.phone_number == sim_data.phone_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SIM card already registered")
    sim = SIMCard(
        network_name=sim_data.network_name,
        phone_number=sim_data.phone_number,
        slot_index=sim_data.slot_index,
        current_float_balance=sim_data.current_float_balance,
        status=SIMStatus.ONLINE,
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return SIMCardResponse.model_validate(sim)


@router.get("", response_model=list[SIMCardResponse])
def list_sim_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from mobile_money_gateway.models.models import SIMCard
    sims = db.query(SIMCard).all()
    return [SIMCardResponse.model_validate(s) for s in sims]


@router.get("/{sim_id}", response_model=SIMCardResponse)
def get_sim_card(
    sim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from mobile_money_gateway.models.models import SIMCard
    sim = db.query(SIMCard).filter(SIMCard.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SIM card not found")
    return SIMCardResponse.model_validate(sim)


@router.patch("/{sim_id}/status")
def update_sim_status(
    sim_id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    from mobile_money_gateway.models.models import SIMCard, SIMStatus
    sim = db.query(SIMCard).filter(SIMCard.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SIM card not found")
    try:
        sim.status = SIMStatus(status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    db.commit()
    return {"message": "Status updated"}
