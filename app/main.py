from fastapi import FastAPI

from app.api import VERSIONS, router as api_router

app = FastAPI(
    title="AI Campaign API",
    description="AI-powered campaign content generation API",
    version="1.0.0",
)

# All versioned endpoints live under /api/<version>/...
app.include_router(api_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-campaign-api",
        "api_versions": VERSIONS,
    }
