"""Read and update the single strategy configuration stored in the database."""

from sqlalchemy.orm import Session

from app.models import StrategyConfigRecord
from app.strategies.ema_rsi_atr import StrategyConfig


def current_strategy_config(db: Session) -> StrategyConfig:
    record = db.get(StrategyConfigRecord, 1)
    if record is None:
        config = StrategyConfig()
        record = StrategyConfigRecord(id=1, payload=config.model_dump(mode="json"))
        db.add(record)
        db.commit()
        return config
    return StrategyConfig.model_validate(record.payload)


def save_strategy_config(db: Session, config: StrategyConfig) -> StrategyConfig:
    config.validate_periods()
    record = db.get(StrategyConfigRecord, 1)
    if record is None:
        record = StrategyConfigRecord(id=1, payload=config.model_dump(mode="json"))
        db.add(record)
    else:
        record.payload = config.model_dump(mode="json")
    db.commit()
    return config
