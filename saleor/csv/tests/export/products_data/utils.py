from .....attribute import AttributeInputType
from .....core.utils.editorjs import clean_editor_js


def add_product_attribute_data_to_expected_data(data, product, attribute_ids, pk=None):
    for assigned_attribute in product.attributes.all():
        if assigned_attribute:
            header = f"{assigned_attribute.attribute.slug} (product attribute)"
            if str(assigned_attribute.attribute.pk) in attribute_ids:
                value = get_attribute_value(assigned_attribute)
                if pk:
                    data[pk][header] = value
                else:
                    data[header] = value
    return data


def add_variant_attribute_data_to_expected_data(data, variant, attribute_ids, pk=None):
    for assigned_attribute in variant.attributes.all():
        header = f"{assigned_attribute.attribute.slug} (variant attribute)"
        if str(assigned_attribute.attribute.pk) in attribute_ids:
            value = get_attribute_value(assigned_attribute)
            if pk:
                data[pk][header] = value
            else:
                data[header] = value

    return data


def get_attribute_value(assigned_attribute):
    value_instance = assigned_attribute.values.first()
    if not value_instance:
        return ""
    attribute = assigned_attribute.attribute
    if attribute.input_type == AttributeInputType.FILE:
        value = "http://mirumee.com/media/" + value_instance.file_url
    elif attribute.input_type == AttributeInputType.REFERENCE:
        ref_id = value_instance.slug.split("_")[1]
        value = f"{attribute.entity_type}_{ref_id}"
    elif attribute.input_type == AttributeInputType.NUMERIC:
        value = f"{value_instance.name}"
        if attribute.unit:
            value += f" {attribute.unit}"
    elif attribute.input_type == AttributeInputType.RICH_TEXT:
        value = clean_editor_js(value_instance.rich_text, to_string=True)
    elif attribute.input_type == AttributeInputType.SWATCH:
        value = (
            value_instance.file_url if value_instance.file_url else value_instance.value
        )
    elif attribute.input_type == AttributeInputType.BOOLEAN:
        value = str(value_instance.boolean)
    elif attribute.input_type == AttributeInputType.DATE:
        value = str(value_instance.date_time.date())
    elif attribute.input_type == AttributeInputType.DATE_TIME:
        value = str(value_instance.date_time)
    else:
        value = value_instance.name or value_instance.slug
    return value


def add_stocks_to_expected_data(data, variant, warehouse_ids, pk=None):
    for stock in variant.stocks.all():
        if str(stock.warehouse.pk) in warehouse_ids:
            slug = stock.warehouse.slug
            warehouse_headers = [
                f"{slug} (warehouse quantity)",
            ]
            if pk:
                data[pk][warehouse_headers[0]] = stock.quantity
            else:
                data[warehouse_headers[0]] = stock.quantity

    return data


def add_channel_to_expected_product_data(data, product, channel_ids, pk=None):
    for channel_listing in product.channel_listings.all():
        if str(channel_listing.channel.pk) in channel_ids:
            channel_slug = channel_listing.channel.slug
            for lookup, field in [
                ("currency_code", "product currency code"),
                ("is_published", "published"),
                ("published_at", "publication date"),
                ("published_at", "published at"),
                ("visible_in_listings", "searchable"),
                ("available_for_purchase_at", "available for purchase"),
            ]:
                header = f"{channel_slug} (channel {field})"
                if lookup == "currency_code":
                    value = getattr(channel_listing, "currency")
                else:
                    value = getattr(channel_listing, lookup)
                if pk:
                    data[pk][header] = value
                else:
                    data[header] = value

    return data


def add_channel_to_expected_variant_data(data, variant, channel_ids, pk=None):
    for channel_listing in variant.channel_listings.all():
        if str(channel_listing.channel.pk) in channel_ids:
            channel_slug = channel_listing.channel.slug
            price_header = f"{channel_slug} (channel price amount)"
            currency_header = f"{channel_slug} (channel variant currency code)"
            cost_price = f"{channel_slug} (channel variant cost price)"
            preorder_quantity_threshold = (
                f"{channel_slug} (channel variant preorder quantity threshold)"
            )
            if pk:
                data[pk][price_header] = channel_listing.price_amount
                data[pk][currency_header] = channel_listing.currency
                data[pk][cost_price] = channel_listing.cost_price_amount
                data[pk][
                    preorder_quantity_threshold
                ] = channel_listing.preorder_quantity_threshold
            else:
                data[price_header] = channel_listing.price_amount
                data[currency_header] = channel_listing.currency
                data[cost_price] = channel_listing.cost_price_amount
                data[
                    preorder_quantity_threshold
                ] = channel_listing.preorder_quantity_threshold
    return data
