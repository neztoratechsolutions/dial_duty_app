from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.auth import router as auth_router
from app.routers.categories import router as category_router
from app.routers.products import router as product_router
from app.routers.product_image import router as product_image_router
from app.routers.product_qa import router as product_qa_router
from app.routers.delivery_areas import router as delivery_areas_router
from app.routers.delivery_boys import router as delivery_boys_router

app = FastAPI(
    title="Dial Duty API",
    description="Dial Duty backend API",
    version="1.0.0",
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


app.include_router(auth_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(product_image_router)
app.include_router(product_qa_router)
app.include_router(delivery_areas_router)
app.include_router(delivery_boys_router)