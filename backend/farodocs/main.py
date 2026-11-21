"""HTTP entry point for the FaroDocs backend."""

from fastapi import FastAPI

app = FastAPI(title="FaroDocs API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Report process liveness; dependency readiness is checked by Compose."""
    return {"status": "ok"}
