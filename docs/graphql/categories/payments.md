# Payments API

Process payments, manage gateways, and handle payment-related operations.

## Available Operations

This category includes 3 operations:

### Queries

#### `payment`

Look up a payment by ID.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `Payment`

#### `payments`

List of payments.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `PaymentCountableConnection`

#### `transaction`

Look up a transaction by ID.
  
  Requires one of the following permissions: HANDLE_PAYMENTS.

**Returns:** `TransactionItem`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
