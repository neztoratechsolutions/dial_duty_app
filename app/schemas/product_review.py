from datetime import datetime
from pydantic import BaseModel,Field,ConfigDict

class ProductReviewCreate(BaseModel):
    product_id : int
    star_rating : int = Field(...,ge=1,le=5)
    description : str | None = None

class ProductReviewResponse(BaseModel):
    id : int 
    user_id: int
    product_id: int
    star_rating: int
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
