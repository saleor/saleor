DOC_CATEGORY_APPS = "Apps"
DOC_CATEGORY_ATTRIBUTES = "Attributes"
DOC_CATEGORY_AUTH = "Authentication"
DOC_CATEGORY_CHANNELS = "Channels"
DOC_CATEGORY_CHECKOUT = "Checkout"
DOC_CATEGORY_DISCOUNTS = "Discounts"
DOC_CATEGORY_GIFT_CARDS = "Gift cards"
DOC_CATEGORY_MENU = "Menu"
DOC_CATEGORY_MISC = "Miscellaneous"
DOC_CATEGORY_ORDERS = "Orders"
DOC_CATEGORY_PAGES = "Pages"
DOC_CATEGORY_PAYMENTS = "Payments"
DOC_CATEGORY_PRODUCTS = "Products"
DOC_CATEGORY_SHIPPING = "Shipping"
DOC_CATEGORY_SHOP = "Shop"
DOC_CATEGORY_TAXES = "Taxes"
DOC_CATEGORY_USERS = "Users"
DOC_CATEGORY_WEBHOOKS = "Webhooks"


# Map models to category names in doc directive.
DOC_CATEGORY_MAP = {
    "account.Address": DOC_CATEGORY_USERS,
    "account.CustomerEvent": DOC_CATEGORY_USERS,
    "account.Group": DOC_CATEGORY_USERS,
    "account.StaffNotificationRecipient": DOC_CATEGORY_USERS,
    "account.User": DOC_CATEGORY_USERS,
    "app.App": DOC_CATEGORY_APPS,
    "app.AppToken": DOC_CATEGORY_APPS,
    "app.AppExtension": DOC_CATEGORY_APPS,
    "app.AppInstallation": DOC_CATEGORY_APPS,
    "attribute.Attribute": DOC_CATEGORY_ATTRIBUTES,
    "attribute.AttributeTranslation": DOC_CATEGORY_ATTRIBUTES,
    "attribute.AttributeValue": DOC_CATEGORY_ATTRIBUTES,
    "attribute.AttributeValueTranslation": DOC_CATEGORY_ATTRIBUTES,
    "channel.Channel": DOC_CATEGORY_CHANNELS,
    "checkout.Checkout": DOC_CATEGORY_CHECKOUT,
    "checkout.CheckoutLine": DOC_CATEGORY_CHECKOUT,
    "discount.Sale": DOC_CATEGORY_DISCOUNTS,
    "discount.SaleTranslation": DOC_CATEGORY_DISCOUNTS,
    "discount.SaleChannelListing": DOC_CATEGORY_DISCOUNTS,
    "discount.Promotion": DOC_CATEGORY_DISCOUNTS,
    "discount.PromotionRule": DOC_CATEGORY_DISCOUNTS,
    "discount.PromotionTranslation": DOC_CATEGORY_DISCOUNTS,
    "discount.PromotionRuleTranslation": DOC_CATEGORY_DISCOUNTS,
    "discount.VoucherChannelListing": DOC_CATEGORY_DISCOUNTS,
    "discount.Voucher": DOC_CATEGORY_DISCOUNTS,
    "discount.VoucherTranslation": DOC_CATEGORY_DISCOUNTS,
    "discount.OrderDiscount": DOC_CATEGORY_DISCOUNTS,
    "invoice.Invoice": DOC_CATEGORY_ORDERS,
    "invoice.InvoiceEvent": DOC_CATEGORY_ORDERS,
    "giftcard.GiftCard": DOC_CATEGORY_GIFT_CARDS,
    "giftcard.GiftCardTag": DOC_CATEGORY_GIFT_CARDS,
    "giftcard.GiftCardEvent": DOC_CATEGORY_GIFT_CARDS,
    "menu.Menu": DOC_CATEGORY_MENU,
    "menu.MenuItem": DOC_CATEGORY_MENU,
    "menu.MenuItemTranslation": DOC_CATEGORY_MENU,
    "order.OrderGrantedRefund": DOC_CATEGORY_ORDERS,
    "order.Order": DOC_CATEGORY_ORDERS,
    "order.OrderLine": DOC_CATEGORY_ORDERS,
    "order.OrderEvent": DOC_CATEGORY_ORDERS,
    "order.Fulfillment": DOC_CATEGORY_ORDERS,
    "order.FulfillmentLine": DOC_CATEGORY_ORDERS,
    "page.Page": DOC_CATEGORY_PAGES,
    "page.PageType": DOC_CATEGORY_PAGES,
    "page.PageTranslation": DOC_CATEGORY_PAGES,
    "payment.Payment": DOC_CATEGORY_PAYMENTS,
    "payment.Transaction": DOC_CATEGORY_PAYMENTS,
    "payment.TransactionItem": DOC_CATEGORY_PAYMENTS,
    "payment.TransactionEvent": DOC_CATEGORY_PAYMENTS,
    "product.Category": DOC_CATEGORY_PRODUCTS,
    "product.CategoryTranslation": DOC_CATEGORY_PRODUCTS,
    "product.Collection": DOC_CATEGORY_PRODUCTS,
    "product.CollectionChannelListing": DOC_CATEGORY_PRODUCTS,
    "product.CollectionTranslation": DOC_CATEGORY_PRODUCTS,
    "product.DigitalContent": DOC_CATEGORY_PRODUCTS,
    "product.DigitalContentUrl": DOC_CATEGORY_PRODUCTS,
    "product.Product": DOC_CATEGORY_PRODUCTS,
    "product.ProductTranslation": DOC_CATEGORY_PRODUCTS,
    "product.ProductChannelListing": DOC_CATEGORY_PRODUCTS,
    "product.ProductMedia": DOC_CATEGORY_PRODUCTS,
    "product.ProductType": DOC_CATEGORY_PRODUCTS,
    "product.ProductVariant": DOC_CATEGORY_PRODUCTS,
    "product.ProductVariantTranslation": DOC_CATEGORY_PRODUCTS,
    "product.ProductVariantChannelListing": DOC_CATEGORY_PRODUCTS,
    "site.SiteSettings": DOC_CATEGORY_SHOP,
    "site.SiteSettingsTranslation": DOC_CATEGORY_SHOP,
    "shipping.ShippingMethodChannelListing": DOC_CATEGORY_SHIPPING,
    "shipping.ShippingMethod": DOC_CATEGORY_SHIPPING,
    "shipping.ShippingMethodTranslation": DOC_CATEGORY_SHIPPING,
    "shipping.ShippingZone": DOC_CATEGORY_SHIPPING,
    "shipping.ShippingMethodPostalCodeRule": DOC_CATEGORY_SHIPPING,
    "tax.TaxConfiguration": DOC_CATEGORY_TAXES,
    "tax.TaxClass": DOC_CATEGORY_TAXES,
    "tax.TaxClassCountryRate": DOC_CATEGORY_TAXES,
    "tax.TaxConfigurationPerCountry": DOC_CATEGORY_TAXES,
    "warehouse.Allocation": DOC_CATEGORY_PRODUCTS,
    "warehouse.Warehouse": DOC_CATEGORY_PRODUCTS,
    "warehouse.Stock": DOC_CATEGORY_PRODUCTS,
    "webhook.WebhookEvent": DOC_CATEGORY_WEBHOOKS,
    "webhook.Webhook": DOC_CATEGORY_WEBHOOKS,
    "core.EventDeliveryAttempt": DOC_CATEGORY_WEBHOOKS,
}
