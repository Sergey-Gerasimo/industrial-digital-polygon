from dataclasses import dataclass, field
from typing import List

from domain.entities.commerce.sales_strategy import SalesStrategy
from domain.entities.commerce.tender import Tender


@dataclass(frozen=True)
class Commerce:
    sales_strategy: SalesStrategy
    tenders: List[Tender] = field(default_factory=list)
