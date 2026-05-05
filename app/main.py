"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="DepWatch",
    description="Dependency Health Scanner — Are your dependencies risky right now?",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
