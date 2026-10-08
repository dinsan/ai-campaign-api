from fastapi import FastAPI, Depends

from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.core.dependencies import get_current_user

app = FastAPI(
    title="AI Campaign API",
    description="AI-powered campaign content generation API",
    version="1.0.0",
)

#registration
app.include_router(
    users_router,
    dependencies=[Depends(get_current_user)])


app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-campaign-api",
    }