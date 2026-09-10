from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from mobile_money_gateway.database import get_db
from mobile_money_gateway.schemas.schemas import BoothCreate, BoothResponse
from mobile_money_gateway.models.models import User, Booth
from mobile_money_gateway.routes.auth_routes import get_current_user, require_role

router = APIRouter(prefix="/booths", tags=["booths"])


@router.post("", response_model=BoothResponse)
def create_booth(
    booth_data: BoothCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    booth = Booth(name=booth_data.name, location=booth_data.location)
    db.add(booth)
    db.commit()
    db.refresh(booth)
    return BoothResponse.model_validate(booth)


@router.get("", response_model=list[BoothResponse])
def list_booths(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booths = db.query(Booth).all()
    return [BoothResponse.model_validate(b) for b in booths]


@router.get("/{booth_id}", response_model=BoothResponse)
def get_booth(
    booth_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booth = db.query(Booth).filter(Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booth not found")
    return BoothResponse.model_validate(booth)
