from fastapi import FastAPI

from app.api.users import router as users_router


app = FastAPI(
    title="AI Campaign API",
    description="AI-powered campaign content generation API",
    version="1.0.0",
)

#user registration
app.include_router(users_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-campaign-api",
    }