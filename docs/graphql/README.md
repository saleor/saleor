# Saleor GraphQL API Documentation

## Overview

Saleor provides a comprehensive GraphQL API that serves as the backbone for all e-commerce operations. This API is designed with an API-first approach, ensuring that all functionality is accessible through well-defined GraphQL operations.

## Quick Start

The Saleor GraphQL API is available at the `/graphql/` endpoint of your Saleor instance. You can explore the API using the built-in GraphQL Playground by navigating to `/graphql/` in your browser.

**👉 [Complete Getting Started Guide](./getting-started.md)**

### Basic Query Example

```graphql
query {
  products(first: 10) {
    edges {
      node {
        id
        name
        slug
        description
      }
    }
  }
}
```

**👉 [View More Examples](./examples.md)**

## API Categories

The Saleor GraphQL API is organized into logical categories for easier navigation and understanding:

### Core Commerce
- **[Products](./categories/products.md)** - Product catalog management, variants, types, and inventory
- **[Orders](./categories/orders.md)** - Order processing, fulfillment, and management
- **[Checkout](./categories/checkout.md)** - Cart management and checkout process

### User Management
- **[Users](./categories/users.md)** - Customer and staff user management
- **[Authentication](./categories/authentication.md)** - Login, logout, and permission management

### Store Configuration
- **[Channels](./categories/channels.md)** - Multi-channel configuration and management
- **[Shop](./categories/shop.md)** - Global shop settings and configuration
- **[Taxes](./categories/taxes.md)** - Tax configuration and calculation

### Marketing & Content
- **[Discounts](./categories/discounts.md)** - Sales, vouchers, and promotional campaigns
- **[Pages](./categories/pages.md)** - CMS pages and content management
- **[Menu](./categories/menu.md)** - Navigation menu management

### Operations
- **[Payments](./categories/payments.md)** - Payment processing and gateway integration
- **[Shipping](./categories/shipping.md)** - Shipping methods and zones
- **[Attributes](./categories/attributes.md)** - Product and page attributes

### Integration
- **[Webhooks](./categories/webhooks.md)** - Event-driven integrations and notifications
- **[Apps](./categories/apps.md)** - Third-party application integration

### Additional Features
- **[Gift Cards](./categories/gift-cards.md)** - Gift card management and processing
- **[Miscellaneous](./categories/miscellaneous.md)** - Utility queries and other operations

## Authentication

Most operations require proper authentication. Saleor supports multiple authentication methods:

- **JWT Tokens** - For user authentication
- **App Tokens** - For application-based access
- **Staff Permissions** - Role-based access control

## Rate Limiting

The API implements rate limiting to ensure fair usage. Consider implementing appropriate caching strategies for production applications.

## Schema Introspection

The GraphQL schema supports full introspection, allowing you to discover all available types, fields, and operations programmatically.

## Error Handling

Saleor GraphQL API follows GraphQL error handling conventions, providing detailed error messages and codes for debugging and user feedback.

## Further Reading

- [GraphQL Specification](https://graphql.org/learn/)
- [Saleor Documentation](https://docs.saleor.io/)
- [API Reference](./reference/)