# Checkout API

Handle cart management, checkout process, and order creation.

## Available Operations

This category includes 2 operations:

### Queries

#### `checkoutLines`

List of checkout lines. The query will not initiate any external requests, including fetching external shipping methods, filtering available shipping methods, or performing external tax calculations.
  
  Requires one of the following permissions: MANAGE_CHECKOUTS.

**Returns:** `CheckoutLineCountableConnection`

#### `checkouts`

List of checkouts. The query will not initiate any external requests, including fetching external shipping methods, filtering available shipping methods, or performing external tax calculations.
  
  Requires one of the following permissions: MANAGE_CHECKOUTS, HANDLE_PAYMENTS.

**Returns:** `CheckoutCountableConnection`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
