from fastapi import FastAPI

app = FastAPI(
    title="AI Campaign API",
    description="AI-powered campaign content generation API",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-campaign-api",
    }