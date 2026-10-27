from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product_review import ProductReview
from app.models.product import Product
from app.routers.users import get_logged_in_user
from app.schemas.product_review import ProductReviewCreate,ProductReviewResponse

router = APIRouter(
    prefix="/product-reviews",
    tags=["Product Reviews"],
)


# 1. Add a review
@router.post("",response_model=ProductReviewResponse,status_code=status.HTTP_201_CREATED)
def create_product_review(
    payload : ProductReviewCreate,
    current_user = Depends(get_logged_in_user),
    db: Session = Depends(get_db)
):
    # Check whether the product exists
    product = db.query(Product).filter(
        Product.id == payload.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code = 404,
            detail="product not found"
        )
    

    # Check whether this user has already reviewed this product
    existing_review = db.query(ProductReview).filter(
        ProductReview.user_id == current_user.id,
        ProductReview.product_id == payload.product_id  
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product",
        )

    review = ProductReview(
        user_id=current_user.id,
        product_id=payload.product_id,
        star_rating=payload.star_rating,
        description=payload.description,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review

# GET: Get all reviews for a product
@router.get(
    "/product/{product_id}",
    response_model=list[ProductReviewResponse]
)
def get_product_review(
    product_id : int,
    db:Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id 
    ).first()

    if not product :
        raise HTTPException(
            status_code = 404,
            detail="Product not found"
        )

    reviews = db.query(ProductReview).filter(
        ProductReview.product_id == product_id
    ).order_by(
        ProductReview.created_at.desc()
    ).all()

    return reviews

# GET: Get reviews submitted by the logged-in user
@router.get("/me")
def get_my_reviews(
    current_user = Depends(get_logged_in_user),
    db:Session = Depends(get_db)
):
    reviews = db.query(ProductReview).filter(
        ProductReview.user_id == current_user.id
    ).order_by(
        ProductReview.created_at.desc()
    ).all()

    return reviews

# DELETE: Delete your own review
@router.delete("/{review_id}")
def delete_product_review(
    review_id : int,
    db:Session = Depends(get_db),
    current_user = Depends(get_logged_in_user)
):
    review = db.query(ProductReview).filter(
        ProductReview.id == review_id,
        ProductReview.user_id == current_user.id
    ).first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    db.delete(review)
    db.commit()

    return {"message": "Product review deleted successfully"}
       