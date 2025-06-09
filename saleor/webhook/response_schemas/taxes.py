from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from ...core.prices import MAXIMUM_PRICE


class LineCalculateTaxesSchema(BaseModel):
    tax_rate: Annotated[Decimal, Field(ge=0)]
    total_gross_amount: Annotated[Decimal, Field(ge=0, le=MAXIMUM_PRICE)]
    total_net_amount: Annotated[Decimal, Field(ge=0, le=MAXIMUM_PRICE)]


class CalculateTaxesSchema(BaseModel):
    shipping_tax_rate: Annotated[Decimal, Field(ge=0)]
    shipping_price_gross_amount: Annotated[Decimal, Field(ge=0, le=MAXIMUM_PRICE)]
    shipping_price_net_amount: Annotated[Decimal, Field(ge=0, le=MAXIMUM_PRICE)]
    lines: list[LineCalculateTaxesSchema] = []

    @field_validator("lines")
    @classmethod
    def clean_lines_length(
        cls, lines: list[LineCalculateTaxesSchema], info: ValidationInfo
    ):
        context = info.context
        if not context:
            raise ValueError("Context is required to validate the number of lines.")

        expected_line_count = context.get("expected_line_count")
        if expected_line_count and len(lines) != expected_line_count:
            raise ValueError(
                f"Number of lines from tax data doesn't match the line number from order. "
                f"Expected {expected_line_count} but got {len(lines)}."
            )
        return lines
