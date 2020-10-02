class ProductExportFields:
    """Data structure with fields for product export."""

    HEADERS_TO_FIELDS_MAPPING = {
        "fields": {
            "id": "id",
            "name": "name",
            "description": "description",
            # TODO: remove this field in SALEOR-902
            "available for purchase": "available_for_purchase",
            "searchable": "visible_in_listings",
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
        "slug": "attributes__assignment__attribute__slug",
        "attribute_pk": "attributes__assignment__attribute__pk",
    }

    PRODUCT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "channel_listing__channel__pk",
        "slug": "channel_listing__channel__slug",
        "product_currency_code": "channel_listing__channel__currency_code",
        "published": "channel_listing__is_published",
        "publication_date": "channel_listing__publication_date",
    }

    WAREHOUSE_FIELDS = {
        "slug": "variants__stocks__warehouse__slug",
        "quantity": "variants__stocks__quantity",
        "warehouse_pk": "variants__stocks__warehouse__id",
    }

    VARIANT_ATTRIBUTE_FIELDS = {
        "value": "variants__attributes__values__slug",
        "slug": "variants__attributes__assignment__attribute__slug",
        "attribute_pk": "variants__attributes__assignment__attribute__pk",
    }

    VARIANT_CHANNEL_LISTING_FIELDS = {
        "channel_pk": "variants__channel_listing__channel__pk",
        "slug": "variants__channel_listing__channel__slug",
        "price_amount": "variants__channel_listing__price_amount",
        "variant_currency_code": "channel_listing__channel__currency_code",
        "variant_cost_price": "variants__channel_listing__cost_price_amount",
    }
