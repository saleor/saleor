# Getting Started with Saleor GraphQL API

## Introduction

The Saleor GraphQL API provides a modern, flexible way to interact with your e-commerce platform. This guide will help you get started with the most common operations.

## API Endpoint

The GraphQL API is available at:
```
https://your-saleor-domain.com/graphql/
```

For local development:
```
http://localhost:8000/graphql/
```

## Authentication

Most operations require authentication. Saleor supports several authentication methods:

### 1. JWT Tokens (User Authentication)
```graphql
mutation {
  tokenCreate(email: "user@example.com", password: "password") {
    token
    user {
      id
      email
    }
    errors {
      field
      message
    }
  }
}
```

Then use the token in subsequent requests:
```
Authorization: Bearer <your-jwt-token>
```

### 2. App Tokens (Application Authentication)
For server-to-server communication, use app tokens in the header:
```
Authorization: Bearer <your-app-token>
```

## Common Operations

### Fetching Products

```graphql
query GetProducts {
  products(first: 10) {
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
        images {
          url
          alt
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

### Creating an Order

```graphql
# 1. Create checkout
mutation CreateCheckout {
  checkoutCreate(input: {
    channel: "default-channel"
    lines: [
      {
        quantity: 1
        variantId: "UHJvZHVjdFZhcmlhbnQ6MQ=="
      }
    ]
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
    }
    errors {
      field
      message
    }
  }
}

# 2. Add shipping address
mutation UpdateShippingAddress($token: UUID!) {
  checkoutShippingAddressUpdate(
    token: $token
    shippingAddress: {
      firstName: "John"
      lastName: "Doe"
      streetAddress1: "123 Main St"
      city: "New York"
      countryCode: US
      postalCode: "10001"
    }
  ) {
    checkout {
      id
      shippingAddress {
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

# 3. Complete checkout
mutation CompleteCheckout($token: UUID!) {
  checkoutComplete(token: $token) {
    order {
      id
      number
      status
      total {
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

### Managing Users

```graphql
# Create a customer account
mutation CreateUser {
  accountRegister(input: {
    email: "customer@example.com"
    password: "secure-password"
    redirectUrl: "https://yoursite.com/confirm-email"
  }) {
    user {
      id
      email
    }
    errors {
      field
      message
    }
  }
}

# Get user profile
query GetUserProfile {
  me {
    id
    email
    firstName
    lastName
    addresses {
      id
      firstName
      lastName
      streetAddress1
      city
      country {
        code
        country
      }
    }
    orders(first: 10) {
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
        }
      }
    }
  }
}
```

## Error Handling

GraphQL operations can return errors in two ways:

### 1. GraphQL Errors
These are returned in the `errors` array of the response:
```json
{
  "data": null,
  "errors": [
    {
      "message": "You do not have permission to perform this action",
      "locations": [{"line": 2, "column": 3}],
      "path": ["products"]
    }
  ]
}
```

### 2. Field-specific Errors
These are returned in the `errors` field of mutation results:
```json
{
  "data": {
    "checkoutCreate": {
      "checkout": null,
      "errors": [
        {
          "field": "lines",
          "message": "Could not resolve to a node with the global id list"
        }
      ]
    }
  }
}
```

## Pagination

Saleor uses cursor-based pagination following the Relay specification:

```graphql
query GetProductsWithPagination($cursor: String) {
  products(first: 10, after: $cursor) {
    edges {
      node {
        id
        name
      }
      cursor
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
```

## Filtering and Sorting

Many list operations support filtering and sorting:

```graphql
query GetFilteredProducts {
  products(
    first: 20
    filter: {
      isPublished: true
      price: { gte: 10, lte: 100 }
      categories: ["Q2F0ZWdvcnk6MQ=="]
    }
    sortBy: { field: PRICE, direction: ASC }
  ) {
    edges {
      node {
        id
        name
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
      }
    }
  }
}
```

## Best Practices

### 1. Use Fragments
Avoid repeating field selections by using GraphQL fragments:

```graphql
fragment ProductBasic on Product {
  id
  name
  slug
  description
}

fragment ProductPricing on Product {
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
}

query GetProducts {
  products(first: 10) {
    edges {
      node {
        ...ProductBasic
        ...ProductPricing
      }
    }
  }
}
```

### 2. Request Only Needed Fields
GraphQL allows you to request exactly the data you need:

```graphql
# Good - only request needed fields
query GetProductNames {
  products(first: 10) {
    edges {
      node {
        id
        name
      }
    }
  }
}

# Avoid - requesting unnecessary data
query GetProducts {
  products(first: 10) {
    edges {
      node {
        id
        name
        description
        images {
          url
          alt
        }
        # ... many other fields you don't need
      }
    }
  }
}
```

### 3. Handle Loading States
Always handle loading states in your application:

```javascript
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
const [data, setData] = useState(null);

// Fetch data
fetch('/graphql/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ query: productQuery })
})
.then(response => response.json())
.then(result => {
  if (result.errors) {
    setError(result.errors);
  } else {
    setData(result.data);
  }
  setLoading(false);
});
```

## Next Steps

- Explore specific [API categories](./categories/) for detailed operations
- Check out the [API Reference](./reference/) for complete schema documentation
- Review [authentication methods](./categories/authentication.md) for secure access
- Learn about [webhook integration](./categories/webhooks.md) for real-time updates