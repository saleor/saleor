from collections import defaultdict

from ...warehouse.models import Allocation
from ..core.dataloaders import DataLoader


class AllocationsByOrderLineIdLoader(DataLoader):
    context_key = "allocations_by_orderline_id"

    def batch_load(self, keys):
        allocations = Allocation.objects.filter(order_line__pk__in=keys).select_related(
            "order_line", "stock"
        )
        order_lines_to_allocations = defaultdict(list)

        for allocation in allocations:
            for order_line_id in keys:
                if allocation.order_line_id == order_line_id:
                    order_lines_to_allocations[order_line_id].append(allocation)

        return [order_lines_to_allocations[order_line_id] for order_line_id in keys]
