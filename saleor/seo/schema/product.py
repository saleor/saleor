IN_STOCK = "http://schema.org/InStock"
OUT_OF_STOCK = "http://schema.org/OutOfStock"


def variant_json_ld(price, variant, in_stock):
    schema_data = {
        "@type": "Offer",
        "itemCondition": "http://schema.org/NewCondition",
        "priceCurrency": price.currency,
        "price": price.amount,
        "sku": variant.sku,
    }
    if in_stock:
        schema_data["availability"] = IN_STOCK
    else:
        schema_data["availability"] = OUT_OF_STOCK
    return schema_data
