def add_product_attribute_data_to_expected_data(data, product, attribute_ids):
    for assigned_attribute in product.attributes.all():
        if assigned_attribute:
            header = f"{assigned_attribute.attribute.slug} (product attribute)"
            if str(assigned_attribute.attribute.pk) in attribute_ids:
                data[header] = assigned_attribute.values.first().slug

    return data


def add_variant_attribute_data_to_expected_data(data, variant, attribute_ids):
    for assigned_attribute in variant.attributes.all():
        header = f"{assigned_attribute.attribute.slug} (variant attribute)"
        if str(assigned_attribute.attribute.pk) in attribute_ids:
            data[header] = assigned_attribute.values.first().slug

    return data


def add_stocks_to_expected_data(data, variant, warehouse_ids):
    for stock in variant.stocks.all():
        if str(stock.warehouse.pk) in warehouse_ids:
            slug = stock.warehouse.slug
            warehouse_headers = [
                f"{slug} (warehouse quantity)",
            ]
            data[warehouse_headers[0]] = stock.quantity

    return data
