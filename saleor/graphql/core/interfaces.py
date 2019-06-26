from dataclasses import dataclass

from ...core.models import SortableModel


@dataclass
class MoveOperation:
    node: SortableModel
    sort_order: int
