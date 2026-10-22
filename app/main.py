from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.auth import router as auth_router
from app.routers.categories import router as category_router
from app.routers.products import router as product_router
from app.routers.product_image import router as product_image_router

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
