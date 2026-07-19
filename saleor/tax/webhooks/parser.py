import logging
from typing import Any

from pydantic import ValidationError

from ...core.taxes import TAX_ERROR_FIELD_LENGTH, TaxData, TaxDataError, TaxLineData
from ...core.utils.text import safe_truncate
from ...webhook.response_schemas.taxes import CalculateTaxesSchema
from ...webhook.response_schemas.utils.helpers import parse_validation_error

logger = logging.getLogger(__name__)


def parse_tax_data(
    event_type: str, response_data: Any, expected_lines_count: int
) -> TaxData:
    try:
        tax_data = _parse_tax_data(response_data, expected_lines_count)
    except ValidationError as e:
        errors = e.errors()
        logger.warning(
            "Webhook response for event %s is invalid: %s",
            event_type,
            str(e),
            extra={"errors": errors},
        )
        error_msg = safe_truncate(parse_validation_error(e), TAX_ERROR_FIELD_LENGTH)
        raise TaxDataError(error_msg, errors=errors) from e
    return tax_data


def _parse_tax_data(
    response_data: Any,
    lines_count: int,
) -> TaxData:
    calculated_taxes_model = CalculateTaxesSchema.model_validate(
        response_data,
        context={"expected_line_count": lines_count},
    )
    return TaxData(
        shipping_price_gross_amount=calculated_taxes_model.shipping_price_gross_amount,
        shipping_price_net_amount=calculated_taxes_model.shipping_price_net_amount,
        shipping_tax_rate=calculated_taxes_model.shipping_tax_rate,
        lines=[
            TaxLineData(
                tax_rate=tax_line.tax_rate,
                total_gross_amount=tax_line.total_gross_amount,
                total_net_amount=tax_line.total_net_amount,
            )
            for tax_line in calculated_taxes_model.lines
        ],
    )
