class ProductExportFields:
    """Data structure with fields for product export."""

    HEADERS_TO_FIELDS_MAPPING = {
        "fields": {
            "id": "id",
            "name": "name",
            "description": "description_as_str",
            "category": "category__slug",
            "product type": "product_type__name",
            "charge taxes": "charge_taxes",
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
        "value_slug": "attributes__values__slug",
        "value_name": "attributes__values__name",
        "file_url": "attributes__values__file_url",
        "rich_text": "attributes__values__rich_text",
        "value": "attributes__values__value",
        "boolean": "attributes__values__boolean",
        "date_time": "attributes__values__date_time",
        "slug": "attributes__assignment__attribute__slug",
        "input_type": "attributes__assignment__attribute__input_type",
        "entity_type": "attributes__assignment__attribute__entity_type",
        "unit": "attributes__assignment__attribute__unit",
        "attribute_pk": "attributes__assignment__attribute__pk",
        "reference_page": "attributes__values__reference_page",
        "reference_product": "attributes__values__reference_product",
        "reference_variant": "attributes__values__reference_variant",
    }

    PRODUCT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "channel_listings__channel__pk",
        "slug": "channel_listings__channel__slug",
        "product_currency_code": "channel_listings__currency",
        "published": "channel_listings__is_published",
        "publication_date": "channel_listings__published_at",
        "published_at": "channel_listings__published_at",
        "searchable": "channel_listings__visible_in_listings",
        "available for purchase": "channel_listings__available_for_purchase_at",
    }

    WAREHOUSE_FIELDS = {
        "slug": "variants__stocks__warehouse__slug",
        "quantity": "variants__stocks__quantity",
        "warehouse_pk": "variants__stocks__warehouse__id",
    }

    VARIANT_ATTRIBUTE_FIELDS = {
        "value_slug": "variants__attributes__values__slug",
        "value_name": "variants__attributes__values__name",
        "file_url": "variants__attributes__values__file_url",
        "rich_text": "variants__attributes__values__rich_text",
        "value": "variants__attributes__values__value",
        "boolean": "variants__attributes__values__boolean",
        "date_time": "variants__attributes__values__date_time",
        "slug": "variants__attributes__assignment__attribute__slug",
        "input_type": "variants__attributes__assignment__attribute__input_type",
        "entity_type": "variants__attributes__assignment__attribute__entity_type",
        "unit": "variants__attributes__assignment__attribute__unit",
        "attribute_pk": "variants__attributes__assignment__attribute__pk",
        "reference_page": "variants__attributes__values__reference_page",
        "reference_product": "variants__attributes__values__reference_product",
        "reference_variant": "variants__attributes__values__reference_variant",
    }

    VARIANT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "variants__channel_listings__channel__pk",
        "slug": "variants__channel_listings__channel__slug",
        "price_amount": "variants__channel_listings__price_amount",
        "variant_currency_code": "variants__channel_listings__currency",
        "variant_cost_price": "variants__channel_listings__cost_price_amount",
        "variant_preorder_quantity_threshold": (
            "variants__channel_listings__preorder_quantity_threshold"
        ),
    }
