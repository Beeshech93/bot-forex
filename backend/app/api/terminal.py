"""Read-only MetaTrader 5 terminal status and symbol routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.security import require_api_token
from app.services.mt5_service import MT5UnavailableError, mt5_service

router = APIRouter(prefix="/api/v1", tags=["terminal"], dependencies=[Depends(require_api_token)])


@router.get("/terminal", summary="Read terminal connection status")
async def terminal_status() -> dict[str, object]:
    result = mt5_service.status()
    return {
        "status": "connected" if result.connected else "disconnected",
        "available": result.available,
        "platform_supported": result.platform_supported,
        "message": result.message,
    }


@router.get("/symbols", summary="List symbols available in the connected terminal")
async def symbols() -> dict[str, object]:
    try:
        items = mt5_service.symbols()
    except MT5UnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "mt5_unavailable", "message": str(exc)},
        ) from exc
    return {"items": items, "count": len(items)}
