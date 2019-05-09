from typing import Dict, Generator, Iterable
from prices import Money

from .event import event


def enhanced_item(
        name: str, unit_price: Money, quantity: int=None, item_id: str=None,
        category: str=None, brand: str=None, variant: str=None,
        **extra_data) -> Dict:
    payload = {
        'nm': name, 'pr': str(unit_price.amount), 'qt': quantity or 1}

    if item_id:
        payload['id'] = item_id
    if category:
        payload['ca'] = category
    if brand:
        payload['br'] = brand
    if variant:
        payload['va'] = variant

    payload.update(extra_data)
    return payload


def enhanced_purchase(
        transaction_id: str, items: Iterable[Dict], revenue: Money,
        url_page: str, tax: Money=None, shipping: Money=None, host: str=None,
        affiliation: str=None, coupon: str=None,
        **extra_data) -> Generator[Dict, None, None]:
    if not items:
        raise ValueError('You need to specify at least one item')

    yield from event('ecommerce', 'purchase')

    payload = {
        'pa': 'purchase', 'ti': transaction_id, 'dp': url_page,
        'tr': str(revenue.amount), 'tt': '0'}

    if shipping:
        payload['ts'] = str(shipping)
    if tax is not None:
        payload['tt'] = str(tax.amount)
    if host:
        payload['dh'] = host
    if affiliation:
        payload['ta'] = affiliation
    if coupon:
        payload['tcc'] = coupon

    payload.update(extra_data)

    for position, item in enumerate(items):
        payload.update(_finalize_enhanced_purchase_item(item, position + 1))

    yield payload


def _finalize_enhanced_purchase_item(item: Dict, position: int) -> Dict:
    position_prefix = 'pr{0}'.format(position)
    final_item = {}
    for key, value in item.items():
        final_item[position_prefix + key] = value
    return final_item
