from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.wishlist import Wishlist
from app.routers.users import get_logged_in_user
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.product import Product

router = APIRouter(
    prefix="/wishlist",
    tags=["Wishlist"]
)

class WishlistCreate(BaseModel):
    product_id : int = Field(gt=0)

# POST: Add a product to wishlist
@router.post("/")
def create_wishlist(
    data:WishlistCreate,
    current_user = Depends(get_logged_in_user),
    db:Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == data.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    existing_product = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == data.product_id
    ).first()

    if existing_product:
        return {
            "message": "Product already in wishlist",
            "wishlist_id": existing_product.id,
            "product_id": existing_product.product_id            
        }

    wishlist_item = Wishlist(
        user_id=current_user.id,
        product_id=data.product_id,
        created_at=datetime.utcnow()       
    )

    db.add(wishlist_item)
    db.commit()
    db.refresh(wishlist_item)

    return {
        "message": "Product added to wishlist",
        "wishlist_id": wishlist_item.id,
        "product_id": wishlist_item.product_id
    }

# GET: View all wishlist products

@router.get("/")
def get_wishlist(
    current_user=Depends(get_logged_in_user),
    db: Session = Depends(get_db)
):
    items = db.query(Wishlist, Product).join(
        Product,
        Wishlist.product_id == Product.id
    ).filter(
        Wishlist.user_id == current_user.id
    ).order_by(
        Wishlist.created_at.desc()
    ).all()

    results = []

    for wishlist_item, product in items:
        results.append({
            "wishlist_id": wishlist_item.id,
            "product_id": product.id,
            "product_name": product.product_name,
            "price": float(product.price),
            "created_at": wishlist_item.created_at
        })

    return results

# DELETE: Remove a product from wishlist
@router.delete("/{product_id}")
def delete_from_wishlist(
    product_id:int,
    current_user = Depends(get_logged_in_user),
    db:Session = Depends(get_db)
):
    wishlist_item = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == product_id
    ).first()

    if not wishlist_item:
        raise HTTPException(
            status_code=404,
            detail="Product not found in your wishlist"
        )

    db.delete(wishlist_item)
    db.commit()

    return {
        "message": "Product removed from wishlist",
        "product_id": product_id
    }