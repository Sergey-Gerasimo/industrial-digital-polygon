from dataclasses import dataclass, field
from typing import List

from domain.entities.production.knowalege import Knowalege
from domain.entities.base.money import Money

# TODO: Реализовать методы сотрудника


@dataclass(frozen=True)
class Employee:
    name: str
    specialization: str
    qualification: str
    sallary: Money
    additional_knowledge: List[Knowalege] = field(default_factory=list)
    tendencies_to_violate_discipline: float
