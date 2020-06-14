from dataclasses import dataclass

@dataclass
class CartAllocationConfiguration:
    validity_time: str
    action_extend_validity: bool
