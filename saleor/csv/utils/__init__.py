class ProductExportFields:
    """Data structure with fields for product export."""

    HEADERS_TO_FIELDS_MAPPING = {
        "fields": {
            "id": "id",
            "name": "name",
            "description": "description",
            "category": "category__slug",
            "product type": "product_type__name",
            "charge taxes": "charge_taxes",
            "product weight": "product_weight",
            "variant sku": "variants__sku",
            "variant weight": "variant_weight",
        },
        "product_many_to_many": {
            "collections": "collections__slug",
            "product images": "images__image",
        },
        "variant_many_to_many": {"variant images": "variants__images__image"},
    }

    PRODUCT_ATTRIBUTE_FIELDS = {
        "value": "attributes__values__slug",
        "file_url": "attributes__values__file_url",
        "slug": "attributes__assignment__attribute__slug",
        "input_type": "attributes__assignment__attribute__input_type",
        "entity_type": "attributes__assignment__attribute__entity_type",
        "attribute_pk": "attributes__assignment__attribute__pk",
    }

    PRODUCT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "channel_listings__channel__pk",
        "slug": "channel_listings__channel__slug",
        "product_currency_code": "channel_listings__currency",
        "published": "channel_listings__is_published",
        "publication_date": "channel_listings__publication_date",
        "searchable": "channel_listings__visible_in_listings",
        "available for purchase": "channel_listings__available_for_purchase",
    }

    WAREHOUSE_FIELDS = {
        "slug": "variants__stocks__warehouse__slug",
        "quantity": "variants__stocks__quantity",
        "warehouse_pk": "variants__stocks__warehouse__id",
    }

    VARIANT_ATTRIBUTE_FIELDS = {
        "value": "variants__attributes__values__slug",
        "file_url": "variants__attributes__values__file_url",
        "slug": "variants__attributes__assignment__attribute__slug",
        "input_type": "variants__attributes__assignment__attribute__input_type",
        "entity_type": "variants__attributes__assignment__attribute__entity_type",
        "attribute_pk": "variants__attributes__assignment__attribute__pk",
    }

    VARIANT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "variants__channel_listings__channel__pk",
        "slug": "variants__channel_listings__channel__slug",
        "price_amount": "variants__channel_listings__price_amount",
        "variant_currency_code": "variants__channel_listings__currency",
        "variant_cost_price": "variants__channel_listings__cost_price_amount",
    }
