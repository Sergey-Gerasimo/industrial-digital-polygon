from dataclasses import dataclass
from enum import Enum


class SalesStrategyType(str, Enum):
    REMOTE_SENSING = "REMOTE_SENSING"
    RETRANSMISSION = "RETRANSMISSION"
    SCIENTIFIC_ACTIVITY = "SCIENTIFIC_ACTIVITY"


@dataclass(frozen=True)
class SalesStrategy:
    sales_strategy_type: SalesStrategyType
