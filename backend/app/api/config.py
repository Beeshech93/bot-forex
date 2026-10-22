"""Authenticated strategy configuration endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_api_token
from app.services.config_service import current_strategy_config, save_strategy_config
from app.strategies.ema_rsi_atr import StrategyConfig

router = APIRouter(prefix="/api/v1", tags=["configuration"], dependencies=[Depends(require_api_token)])


@router.get("/config", summary="Read strategy parameters")
def read_config(db: Session = Depends(get_db)) -> dict[str, object]:
    return current_strategy_config(db).model_dump(mode="json")


@router.put("/config", summary="Save validated strategy parameters")
def update_config(payload: StrategyConfig, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return save_strategy_config(db, payload).model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_config", "message": str(exc)}) from exc
