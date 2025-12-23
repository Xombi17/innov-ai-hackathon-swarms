from pydantic import BaseModel
from enum import Enum

class ConstraintType(Enum):
    BUDGET = "budget"
    TIME = "time"
    PREFERENCE = "preference"

class Constraint(BaseModel):
    type: ConstraintType
    limit: float # value for the limit (e.g., amount of money, minutes)
    description: str
    strictness: float = 1.0 # 0.0 to 1.0, how hard is this constraint?
