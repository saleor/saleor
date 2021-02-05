from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Union

from ....attribute import AttributeInputType, AttributeType

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ....page.models import Page


@dataclass
class AttrValuesInput:
    global_id: str
    values: List[str]
    references: Union[List[str], List["Page"]]
    file_url: Optional[str] = None
    content_type: Optional[str] = None


def get_variant_selection_attributes(qs: "QuerySet"):
    return qs.filter(
        input_type__in=AttributeInputType.ALLOWED_IN_VARIANT_SELECTION,
        type=AttributeType.PRODUCT_TYPE,
    )
