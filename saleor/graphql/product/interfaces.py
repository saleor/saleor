from dataclasses import dataclass
from typing import List

from ...product import models


@dataclass(frozen=True)
class ResolvedAttributeInput:
    instance: models.Attribute
    values: List[str]
