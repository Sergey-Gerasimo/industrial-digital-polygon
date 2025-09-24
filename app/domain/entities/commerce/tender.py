from dataclasses import dataclass
from enum import Enum
from typing import Union

from domain.values.cost import Cost
from domain.values.period import Period
from domain.values.quantity import Quantity


class TenderType(str, Enum):
    GOVERNMENT = "government"
    COMMERCIAL = "commercial"


@dataclass(frozen=True)
class Tender:
    order_cost: Cost
    cost_price: Cost
    quantity: Quantity
    tender_type: TenderType
    penalty_per_day: Cost
    warranty_period: Period
