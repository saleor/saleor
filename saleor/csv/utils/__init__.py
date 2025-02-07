class ProductExportFields:
    """Data structure with fields for product export."""

    HEADERS_TO_FIELDS_MAPPING = {
        "fields": {
            "id": "id",
            "name": "name",
            "description": "description_as_str",
            "category": "category__slug",
            "product type": "product_type__name",
            # charge taxes are deprecated, and do not return any value. In case of
            # requesting them, the headers number needs to match to the size of the row
            "charge taxes": "",  # deprecated; remove in Saleor 4.0
            "product weight": "product_weight",
            "variant id": "variants__id",
            "variant sku": "variants__sku",
            "variant weight": "variant_weight",
            "variant is preorder": "variants__is_preorder",
            "variant preorder global threshold": "variants__preorder_global_threshold",
            "variant preorder end date": "variants__preorder_end_date",
        },
        "product_many_to_many": {
            "collections": "collections__slug",
            "product media": "media__image",
        },
        "variant_many_to_many": {"variant media": "variants__media__image"},
    }

    PRODUCT_ATTRIBUTE_FIELDS = {
        "value_slug": "attributevalues__value__slug",
        "value_name": "attributevalues__value__name",
        "file_url": "attributevalues__value__file_url",
        "rich_text": "attributevalues__value__rich_text",
        "value": "attributevalues__value__value",
        "boolean": "attributevalues__value__boolean",
        "date_time": "attributevalues__value__date_time",
        "slug": "attributevalues__value__attribute__slug",
        "input_type": "attributevalues__value__attribute__input_type",
        "entity_type": "attributevalues__value__attribute__entity_type",
        "unit": "attributevalues__value__attribute__unit",
        "attribute_pk": "attributevalues__value__attribute__pk",
        "reference_page": "attributevalues__value__reference_page",
        "reference_product": "attributevalues__value__reference_product",
        "reference_variant": "attributevalues__value__reference_variant",
    }

    PRODUCT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "channel_id",
        "slug": "channel__slug",
        "product_currency_code": "currency",
        "published": "is_published",
        "publication_date": "published_at",
        "published_at": "published_at",
        "searchable": "visible_in_listings",
        "available for purchase": "available_for_purchase_at",
    }

    WAREHOUSE_FIELDS = {
        "slug": "variants__stocks__warehouse__slug",
        "quantity": "variants__stocks__quantity",
        "warehouse_pk": "variants__stocks__warehouse__id",
    }

    VARIANT_ATTRIBUTE_FIELDS = {
        "value_slug": "values__slug",
        "value_name": "values__name",
        "file_url": "values__file_url",
        "rich_text": "values__rich_text",
        "value": "values__value",
        "boolean": "values__boolean",
        "date_time": "values__date_time",
        "slug": "assignment__attribute__slug",
        "input_type": "assignment__attribute__input_type",
        "entity_type": "assignment__attribute__entity_type",
        "unit": "assignment__attribute__unit",
        "attribute_pk": "assignment__attribute__pk",
        "reference_page": "values__reference_page",
        "reference_product": "values__reference_product",
        "reference_variant": "values__reference_variant",
    }

    VARIANT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "channel__pk",
        "slug": "channel__slug",
        "price_amount": "price_amount",
        "variant_currency_code": "currency",
        "variant_cost_price": "cost_price_amount",
        "variant_preorder_quantity_threshold": "preorder_quantity_threshold",
    }
