DRAFT_ORDER_UPDATE_FIELDS = {
    "base_shipping_price_amount",
    "billing_address",
    "channel",
    "collection_point",
    "collection_point_name",
    "customer_note",
    "display_gross_prices",
    "draft_save_billing_address",
    "draft_save_shipping_address",
    "external_reference",
    "language_code",
    "metadata",
    "private_metadata",
    "redirect_url",
    "search_vector",
    "shipping_address",
    "user",
    "user_email",
    "voucher",
    "voucher_code",
    "weight",
}


SHIPPING_METHOD_UPDATE_FIELDS = {
    "base_shipping_price_amount",
    "currency",
    "shipping_method",
    "shipping_method_name",
    "shipping_price_gross_amount",
    "shipping_price_net_amount",
    "shipping_tax_class",
    "shipping_tax_class_metadata",
    "shipping_tax_class_name",
    "shipping_tax_class_private_metadata",
    "shipping_tax_rate",
    "should_refresh_prices",  # to be removed after orderUpdateShipping refactor
    "undiscounted_base_shipping_price_amount",
    "updated_at",  # to be removed after orderUpdateShipping refactor
}
