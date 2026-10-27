from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.reward import RewardTransaction
from app.routers.users import get_logged_in_user

router = APIRouter(
    prefix="/rewards",
    tags=["Rewards"]
)


@router.get("/me")
def get_rewards(
    db:Session = Depends(get_db),
    current_user = Depends(get_logged_in_user)
):
    transactions = db.query(RewardTransaction).filter(
        RewardTransaction.user_id == current_user.id
    ).all()

    total_earned = sum(
        t.points for t in transactions if t.transaction_type == "earned"
    )
    total_used = sum(
        t.points for t in transactions if t.transaction_type == "used"
    )
    total_expired = sum(
        t.points for t in transactions if t.transaction_type == "expired"
    )

    return {
        "total_earned": total_earned,
        "total_used": total_used,
        "total_expired": total_expired,
        "available_points": total_earned - total_used - total_expired,
    }



@router.get("/history")
def reward_history(
    current_user=Depends(get_logged_in_user),
    db: Session = Depends(get_db)
):
    history = db.query(RewardTransaction).filter(
        RewardTransaction.user_id == current_user.id
    ).order_by(
        RewardTransaction.created_at.desc()
    ).all()

    return [
        {
            "id": r.id,
            "transaction_type": r.transaction_type,
            "points": r.points,
            "description": r.description,
            "order_reference": r.order_reference,
            "created_at": r.created_at
        }
        for r in history
    ]









