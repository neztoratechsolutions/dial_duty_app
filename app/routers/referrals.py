from datetime import datetime
from secrets import token_urlsafe
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.referral import Referral,ReferralCode
from app.routers.users import get_logged_in_user

router = APIRouter(
    prefix="/referrals",
    tags=["Referrals"]
)

def get_or_create_code(
        db:Session,user_id:int
):
    code_record = db.query(ReferralCode).filter(
        ReferralCode.user_id == user_id
    ).first()

    if code_record:
        return code_record

    for _ in range(5):
        code = token_urlsafe(8).replace("-","").replace("_","")[:10].upper()
        exists = db.query(ReferralCode).filter(
            ReferralCode.code == code
        ).first()

        if not exists:
            code_record = ReferralCode(code=code,user_id=user_id)
            db.add(code_record)
            db.commit()
            db.refresh(code_record)

            return code_record
    raise HTTPException(status_code=500, detail="Could not generate referral code")


@router.get("/me")
def my_referral_summary(
    current_user=Depends(get_logged_in_user),
    db: Session = Depends(get_db)
):
    code_record = get_or_create_code(db, current_user.id)

    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user.id
    ).all()

    # Add rewards from completed referrals
    total_earned = sum(
        float(r.reward_amount or 0)
        for r in referrals
        if r.status == "completed"
    )

    # Count completed referrals as joined friends
    friends_joined = sum(
        1 for r in referrals
        if r.status == "completed"
    )

    # Count pending referrals
    pending = sum(
        1 for r in referrals
        if r.status == "pending"
    )

    return {
        "referral_code": code_record,
        "total_earned": total_earned,
        "friends_joined": friends_joined,
        "pending": pending
    }

@router.get("/history")
def referral_history(
    current_user = Depends(get_logged_in_user),
    db: Session = Depends(get_db)
):
    referral = db.query(Referral).filter(
        Referral.referrer_id == current_user.id
    ).order_by(
        Referral.created_at.desc()
    ).all()

    return[
        {
            "id": r.id,
            "referred_user_id": r.referred_user_id,
            "status": r.status,
            "reward_amount": float(r.reward_amount or 0),
            "created_at": r.created_at,
            "credited_at": r.credited_at,
        }
        for r in referral
    ]

@router.get("/users")
def referred_users(
    db:Session = Depends(get_db),
    current_user = Depends(get_logged_in_user)
):
    from app.models.user import User

    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user.id
    ).order_by(
        Referral.created_at.desc()
    ).all()

    results=[]

    for referral in referrals:
        user = db.query(User).filter(
            User.id == referral.referred_user_id
        ).first()

        if user:
            results.append(
                {
                    "user_id": user.id,
                    "name": user.name,
                    "status": referral.status,
                    "joined_at": referral.created_at,
                }
            )
    return results

