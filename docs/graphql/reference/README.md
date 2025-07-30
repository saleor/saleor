# GraphQL API Reference

This directory contains the complete API reference documentation for the Saleor GraphQL API.

## Structure

The API reference is organized by categories, matching the structure of the main API:

- [Products](../categories/products.md) - Product catalog operations
- [Orders](../categories/orders.md) - Order management operations  
- [Users](../categories/users.md) - User and customer management
- [Checkout](../categories/checkout.md) - Shopping cart and checkout
- [Payments](../categories/payments.md) - Payment processing
- [Discounts](../categories/discounts.md) - Promotions and vouchers
- [Attributes](../categories/attributes.md) - Product attributes
- [Shipping](../categories/shipping.md) - Shipping methods and zones
- [Taxes](../categories/taxes.md) - Tax configuration
- [Webhooks](../categories/webhooks.md) - Event notifications
- [Apps](../categories/apps.md) - Third-party integrations
- [Channels](../categories/channels.md) - Multi-channel management
- [Pages](../categories/pages.md) - CMS content
- [Menu](../categories/menu.md) - Navigation menus
- [Gift Cards](../categories/gift-cards.md) - Gift card operations
- [Authentication](../categories/authentication.md) - User authentication
- [Shop](../categories/shop.md) - Global settings
- [Miscellaneous](../categories/miscellaneous.md) - Utility operations

## Schema Statistics

📊 **[View detailed API statistics](../stats.md)**

The Saleor GraphQL API contains extensive functionality across multiple categories, providing comprehensive e-commerce capabilities through a single, unified interface.

## Types Overview

### Core Types
- `Product` - Represents a product in the catalog
- `ProductVariant` - A specific variant of a product
- `Order` - A customer order
- `User` - A user account (customer or staff)
- `Checkout` - A shopping cart/checkout session

### Connection Types
Most list operations return connection types following the Relay specification:
- `ProductConnection`
- `OrderConnection` 
- `UserConnection`
- etc.

### Input Types
Input types are used for mutations and filtering:
- `ProductInput`
- `OrderFilterInput`
- `CheckoutCreateInput`
- etc.

### Enum Types
Enums define specific allowed values:
- `OrderStatus`
- `PaymentChargeStatusEnum`
- `ProductTypeKindEnum`
- etc.

## Directives

### @doc
Used to categorize API operations:
```graphql
@doc(category: "Products")
```

### @deprecated  
Marks deprecated fields with migration information:
```graphql
@deprecated(reason: "Use newField instead")
```

### @webhookEventsInfo
Documents webhook events triggered by operations:
```graphql
@webhookEventsInfo(
  asyncEvents: [ORDER_CREATED]
  syncEvents: [CHECKOUT_CALCULATE_TAXES]
)
```

## Schema Introspection

The API supports full GraphQL introspection. You can query the schema itself:

```graphql
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      description
    }
  }
}
```

## Tools and Resources

- **GraphQL Playground** - Interactive API explorer at `/graphql/`
- **Schema Definition** - Complete schema in `saleor/graphql/schema.graphql`
- **Documentation Generator** - Automated docs via `poetry run poe generate-docs`

---

For detailed usage examples and getting started information, see the [main documentation](../README.md).