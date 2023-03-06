from typing import Union

from django import template
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

register = template.Library()


def _get_display_price(
    base: Union[TaxedMoney, TaxedMoneyRange], display_gross: bool
) -> Money:
    """Return the price amount that should be displayed based on settings."""
    if isinstance(base, TaxedMoneyRange):
        if display_gross:
            base = MoneyRange(start=base.start.gross, stop=base.stop.gross)
        else:
            base = MoneyRange(start=base.start.net, stop=base.stop.net)

    if isinstance(base, TaxedMoney):
        base = base.gross if display_gross else base.net
    return base


@register.inclusion_tag("price.html")
def price(base, display_gross, html=True):
    if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
        base = _get_display_price(base, display_gross)

    is_range = isinstance(base, MoneyRange)
    return {"price": base, "is_range": is_range, "html": html}
