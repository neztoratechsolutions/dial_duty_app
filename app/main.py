from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from app.routers import wishlist
from app.routers import reels
from app.routers.users import router as auth_router
from app.routers.categories import router as categories_router
from app.routers import referrals,rewards
from app.routers.products import router as product_router
from app.routers.stores import router as stores_router
from app.routers.product_image import router as product_image_router
from app.routers.product_qa import router as product_qa_router
from app.routers.delivery_areas import router as delivery_areas_router
from app.routers.delivery_boys import router as delivery_boys_router
from app.routers.admin import router as admin_router
from app.routers import product_reviews
from app.routers import services
from app.routers import qc_staff






app = FastAPI(
    title="Dial Duty API",
    description="Dial Duty backend API",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(reels.router)
app.include_router(referrals.router)
app.include_router(rewards.router)
app.include_router(wishlist.router)
app.include_router(product_router)
app.include_router(stores_router)
app.include_router(product_image_router)
app.include_router(product_qa_router)
app.include_router(delivery_areas_router)
app.include_router(delivery_boys_router)
app.include_router(product_reviews.router)
app.include_router(admin_router)
app.include_router(services.router)
app.include_router(qc_staff.router)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)