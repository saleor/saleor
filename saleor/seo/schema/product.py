from django.utils.encoding import smart_text

IN_STOCK = 'http://schema.org/InStock'
OUT_OF_STOCK = 'http://schema.org/OutOfStock'


def get_brand_from_attributes(attributes):
    if attributes is None:
        return
    brand = ''
    for key in attributes:
        if key.name == 'brand':
            brand = attributes[key].name
            break
        elif key.name == 'publisher':
            brand = attributes[key].name
    return brand


def product_json_ld(product, attributes=None):
    # type: (saleor.product.models.Product, saleor.product.utils.ProductAvailability, dict) -> dict  # noqa
    """Generate JSON-LD data for product."""
    data = {'@context': 'http://schema.org/',
            '@type': 'Product',
            'name': smart_text(product),
            'image': [
                product_image.image.url
                for product_image in product.images.all()],
            'description': product.description,
            'offers': []}

    for variant in product.variants.all():
        price = variant.get_price()
        in_stock = True
        if not product.is_available() or not variant.is_in_stock():
            in_stock = False
        variant_data = variant_json_ld(price, variant, in_stock)
        data['offers'].append(variant_data)

    brand = get_brand_from_attributes(attributes)
    if brand:
        data['brand'] = {'@type': 'Thing', 'name': brand}
    return data


def variant_json_ld(price, variant, in_stock):
    schema_data = {
        '@type': 'Offer',
        'itemCondition': 'http://schema.org/NewCondition',
        'priceCurrency': price.currency,
        'price': price.net.amount,
        'sku': variant.sku}
    if in_stock:
        schema_data['availability'] = IN_STOCK
    else:
        schema_data['availability'] = OUT_OF_STOCK
    return schema_data
