"""Public, non-sensitive health endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check API availability")
async def health() -> dict[str, str]:
    """Return only basic service availability, without account or host details."""
    return {"status": "ok", "service": "smart-signals-fx-api"}
