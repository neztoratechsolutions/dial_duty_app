
from app.database import Base, engine
from app.models import (
    Role,
    User,
    Category,
    DeliveryArea,
    Store,
    DeliveryBoy,
    Product,
    ProductQA,
    Coupon,
)
from app.models.reel import Reel
from app.models.referral import Referral, ReferralCode
from app.models.reward import RewardTransaction
from app.models.wishlist import Wishlist
from app.models.admin import StoreAdmin
from app.models.product_image import ProductImage
from app.models.product_review import ProductReview


def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")

        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"- {table_name}")

    except Exception as error:
        print(f"Error creating tables: {error}")


if __name__ == "__main__":
    create_tables()
