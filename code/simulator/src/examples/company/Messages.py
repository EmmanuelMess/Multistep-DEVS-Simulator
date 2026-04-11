from dataclasses import dataclass

from src.devs.Types import Id


@dataclass
class Product:
    id: Id
    product_type: str


@dataclass
class DemandProduct:
    id: Id
    product_type: str


@dataclass
class OfferProduct:
    id: Id
    product_type: str
    cost: float


@dataclass
class Capital:
    id: Id
    amount: float


@dataclass
class Payment:
    id: Id
    amount: float


@dataclass
class Employee:
    id: Id


@dataclass
class EmployeeOffering:
    id: Id
    employee: Employee


@dataclass
class EmployeeResignation:
    id: Id
    employee: Employee


@dataclass
class LookingForEmployee:
    id: Id


@dataclass
class FireEmployee:
    id: Id
    employee: Employee


@dataclass
class AssignEmployee:
    id: Id
    employee: Employee


@dataclass
class UnassignEmployee:
    id: Id
    employee: Employee


@dataclass
class ForceHaltProduction:
    id: Id


@dataclass
class UndoHaltProduction:
    id: Id


@dataclass
class RequestEmployee:
    id: Id
    sender: str


@dataclass
class StartImprovements:
    id: Id
    product_type: str


@dataclass
class Improvement:
    id: Id
    product_type: str
    efficiency_gain: float


@dataclass
class ImprovementsCost:
    id: Id
    cost: float


@dataclass
class InformImprovementFinished:
    id: Id
    product_type: str
