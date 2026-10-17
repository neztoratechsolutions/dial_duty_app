
from fastapi import FastAPI

app = FastAPI(
    title="Dial Duty API",
    description="Dial Duty backend API",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "success": True,
        "message": "Dial Duty API is running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
