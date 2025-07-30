# GraphQL API Examples

This document provides practical examples for common e-commerce workflows using the Saleor GraphQL API.

## Product Management

### Fetching Product Catalog

```graphql
query GetProductCatalog {
  products(first: 20, filter: { isPublished: true }) {
    edges {
      node {
        id
        name
        slug
        description
        category {
          id
          name
          slug
        }
        collections {
          id
          name
          slug
        }
        pricing {
          priceRange {
            start {
              gross {
                amount
                currency
              }
            }
            stop {
              gross {
                amount
                currency
              }
            }
          }
        }
        variants {
          id
          name
          sku
          pricing {
            price {
              gross {
                amount
                currency
              }
            }
          }
          quantityAvailable
        }
        images {
          id
          url
          alt
        }
        attributes {
          attribute {
            id
            name
            slug
          }
          values {
            id
            name
            slug
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### Creating a Product (Staff Only)

```graphql
mutation CreateProduct {
  productCreate(input: {
    productType: "UHJvZHVjdFR5cGU6MQ=="
    category: "Q2F0ZWdvcnk6MQ=="
    name: "New Product"
    slug: "new-product"
    description: "Product description"
    seo: {
      title: "New Product - SEO Title"
      description: "SEO description for the product"
    }
    weight: 1.5
    attributes: [
      {
        id: "QXR0cmlidXRlOjE="
        values: ["Value1", "Value2"]
      }
    ]
  }) {
    product {
      id
      name
      slug
    }
    errors {
      field
      message
    }
  }
}
```

## Order Management

### Complete Order Flow

```graphql
# Step 1: Create checkout
mutation CreateCheckout {
  checkoutCreate(input: {
    channel: "default-channel"
    lines: [
      {
        quantity: 2
        variantId: "UHJvZHVjdFZhcmlhbnQ6MQ=="
      },
      {
        quantity: 1
        variantId: "UHJvZHVjdFZhcmlhbnQ6Mg=="
      }
    ]
    email: "customer@example.com"
  }) {
    checkout {
      id
      token
      totalPrice {
        gross {
          amount
          currency
        }
      }
      lines {
        id
        quantity
        variant {
          id
          name
          product {
            name
          }
        }
        totalPrice {
          gross {
            amount
            currency
          }
        }
      }
    }
    errors {
      field
      message
    }
  }
}

# Step 2: Add shipping address
mutation AddShippingAddress($token: UUID!) {
  checkoutShippingAddressUpdate(
    token: $token
    shippingAddress: {
      firstName: "John"
      lastName: "Doe"
      companyName: "Acme Corp"
      streetAddress1: "123 Main Street"
      streetAddress2: "Apt 4B"
      city: "New York"
      postalCode: "10001"
      countryCode: US
      phone: "+1-555-123-4567"
    }
  ) {
    checkout {
      id
      shippingAddress {
        firstName
        lastName
        streetAddress1
        city
      }
      availableShippingMethods {
        id
        name
        price {
          amount
          currency
        }
      }
    }
    errors {
      field
      message
    }
  }
}

# Step 3: Select shipping method
mutation SelectShippingMethod($token: UUID!, $shippingMethodId: ID!) {
  checkoutShippingMethodUpdate(
    token: $token
    shippingMethodId: $shippingMethodId
  ) {
    checkout {
      id
      shippingMethod {
        id
        name
      }
      totalPrice {
        gross {
          amount
          currency
        }
      }
    }
    errors {
      field
      message
    }
  }
}

# Step 4: Add billing address
mutation AddBillingAddress($token: UUID!) {
  checkoutBillingAddressUpdate(
    token: $token
    billingAddress: {
      firstName: "John"
      lastName: "Doe"
      streetAddress1: "123 Main Street"
      city: "New York"
      postalCode: "10001"
      countryCode: US
    }
  ) {
    checkout {
      id
      billingAddress {
        firstName
        lastName
      }
    }
    errors {
      field
      message
    }
  }
}

# Step 5: Complete checkout
mutation CompleteCheckout($token: UUID!) {
  checkoutComplete(token: $token) {
    order {
      id
      number
      status
      created
      userEmail
      total {
        gross {
          amount
          currency
        }
      }
      lines {
        id
        quantity
        variant {
          name
          product {
            name
          }
        }
      }
      shippingAddress {
        firstName
        lastName
        streetAddress1
        city
      }
    }
    errors {
      field
      message
    }
  }
}
```

### Fetching Order History

```graphql
query GetOrderHistory($userId: ID!) {
  user(id: $userId) {
    orders(first: 20) {
      edges {
        node {
          id
          number
          created
          status
          total {
            gross {
              amount
              currency
            }
          }
          lines {
            id
            quantity
            variant {
              name
              product {
                name
                thumbnail {
                  url
                }
              }
            }
            unitPrice {
              gross {
                amount
                currency
              }
            }
          }
          shippingAddress {
            firstName
            lastName
            streetAddress1
            city
          }
          fulfillments {
            id
            status
            trackingNumber
            lines {
              id
              quantity
            }
          }
        }
      }
    }
  }
}
```

## User Management

### Customer Registration and Profile

```graphql
# Register new customer
mutation RegisterCustomer {
  accountRegister(input: {
    email: "newcustomer@example.com"
    password: "securePassword123"
    firstName: "Jane"
    lastName: "Smith"
    redirectUrl: "https://mystore.com/account-confirmed"
  }) {
    user {
      id
      email
      firstName
      lastName
    }
    errors {
      field
      message
    }
  }
}

# Update customer profile
mutation UpdateCustomerProfile {
  accountUpdate(input: {
    firstName: "Jane"
    lastName: "Smith-Johnson"
    defaultBillingAddress: {
      firstName: "Jane"
      lastName: "Smith-Johnson"
      streetAddress1: "456 Oak Avenue"
      city: "Los Angeles"
      countryCode: US
      postalCode: "90210"
    }
    defaultShippingAddress: {
      firstName: "Jane"
      lastName: "Smith-Johnson"
      streetAddress1: "456 Oak Avenue"
      city: "Los Angeles"
      countryCode: US
      postalCode: "90210"
    }
  }) {
    user {
      id
      firstName
      lastName
      defaultBillingAddress {
        streetAddress1
        city
      }
      defaultShippingAddress {
        streetAddress1
        city
      }
    }
    errors {
      field
      message
    }
  }
}
```

## Discount Management

### Applying Vouchers and Sales

```graphql
# Check available vouchers
query GetVouchers {
  vouchers(first: 10, filter: { status: ACTIVE }) {
    edges {
      node {
        id
        name
        code
        discountValueType
        discountValue
        minCheckoutItemsQuantity
        usageLimit
        used
        startDate
        endDate
        applyOncePerCustomer
        onlyForStaff
      }
    }
  }
}

# Apply voucher to checkout
mutation ApplyVoucher($token: UUID!, $promoCode: String!) {
  checkoutAddPromoCode(token: $token, promoCode: $promoCode) {
    checkout {
      id
      voucherCode
      discount {
        amount
        currency
      }
      totalPrice {
        gross {
          amount
          currency
        }
      }
    }
    errors {
      field
      message
    }
  }
}

# Remove voucher from checkout
mutation RemoveVoucher($token: UUID!, $promoCode: String!) {
  checkoutRemovePromoCode(token: $token, promoCode: $promoCode) {
    checkout {
      id
      voucherCode
      totalPrice {
        gross {
          amount
          currency
        }
      }
    }
    errors {
      field
      message
    }
  }
}
```

## Inventory Management

### Stock Operations

```graphql
# Check stock levels
query GetStockLevels {
  productVariants(first: 50) {
    edges {
      node {
        id
        name
        sku
        product {
          name
        }
        stocks {
          id
          warehouse {
            id
            name
          }
          quantity
          quantityAllocated
        }
        quantityAvailable
      }
    }
  }
}

# Update stock (Staff only)
mutation UpdateStock($variantId: ID!, $stocks: [StockInput!]!) {
  productVariantStocksUpdate(variantId: $variantId, stocks: $stocks) {
    productVariant {
      id
      stocks {
        warehouse {
          name
        }
        quantity
      }
    }
    errors {
      field
      message
    }
  }
}
```

## Search and Filtering

### Advanced Product Search

```graphql
query SearchProducts($search: String!, $filters: ProductFilterInput) {
  products(
    first: 20
    filter: $filters
    sortBy: { field: RANK, direction: DESC }
  ) {
    edges {
      node {
        id
        name
        slug
        description
        pricing {
          priceRange {
            start {
              gross {
                amount
                currency
              }
            }
          }
        }
        thumbnail {
          url
          alt
        }
        category {
          name
        }
        attributes {
          attribute {
            name
          }
          values {
            name
          }
        }
      }
    }
    totalCount
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# Example variables:
# {
#   "search": "t-shirt",
#   "filters": {
#     "search": "t-shirt",
#     "isPublished": true,
#     "price": { "gte": 10, "lte": 50 },
#     "categories": ["Q2F0ZWdvcnk6MQ=="],
#     "attributes": [
#       {
#         "slug": "color",
#         "values": ["red", "blue"]
#       }
#     ]
#   }
# }
```

## Payment Processing

### Payment Flow

```graphql
# Get available payment gateways
query GetPaymentGateways($channel: String!) {
  shop {
    availablePaymentGateways(channel: $channel) {
      id
      name
      currencies
      config {
        field
        value
      }
    }
  }
}

# Create payment
mutation CreatePayment($checkoutId: ID!, $input: PaymentInput!) {
  checkoutPaymentCreate(checkoutId: $checkoutId, input: $input) {
    payment {
      id
      gateway
      isActive
      total {
        amount
        currency
      }
      chargeStatus
    }
    errors {
      field
      message
    }
  }
}
```

## Webhook Management

### Setting up Webhooks

```graphql
# Create webhook
mutation CreateWebhook {
  webhookCreate(input: {
    name: "Order Created Webhook"
    targetUrl: "https://myapp.com/webhooks/order-created"
    events: [ORDER_CREATED]
    isActive: true
  }) {
    webhook {
      id
      name
      targetUrl
      isActive
      events {
        eventType
      }
    }
    errors {
      field
      message
    }
  }
}

# List webhooks
query GetWebhooks {
  webhooks(first: 20) {
    edges {
      node {
        id
        name
        targetUrl
        isActive
        events {
          eventType
        }
        app {
          id
          name
        }
      }
    }
  }
}
```

## Error Handling Examples

### Handling Common Errors

```javascript
// Example error handling in JavaScript
async function handleGraphQLRequest(query, variables = {}) {
  try {
    const response = await fetch('/graphql/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        query,
        variables
      })
    });

    const result = await response.json();

    // Handle GraphQL errors
    if (result.errors) {
      console.error('GraphQL errors:', result.errors);
      throw new Error(result.errors[0].message);
    }

    // Handle field-specific errors in mutations
    if (result.data && result.data.errors) {
      const fieldErrors = result.data.errors;
      fieldErrors.forEach(error => {
        console.error(`Field ${error.field}: ${error.message}`);
      });
      throw new Error('Validation errors occurred');
    }

    return result.data;

  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Usage example
try {
  const products = await handleGraphQLRequest(`
    query GetProducts {
      products(first: 10) {
        edges {
          node {
            id
            name
          }
        }
      }
    }
  `);
  console.log('Products:', products.products);
} catch (error) {
  // Handle error appropriately
  showErrorMessage(error.message);
}
```

These examples demonstrate common patterns and workflows when working with the Saleor GraphQL API. For more specific operations, refer to the individual [category documentation](./categories/).