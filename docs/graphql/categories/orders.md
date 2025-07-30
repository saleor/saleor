# Orders API

Handle order processing, fulfillment, and management operations.

## Available Operations

This category includes 5 operations:

### Queries

#### `homepageEvents`

List of activity events to display on homepage (at the moment it only contains order-events).
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `OrderEventCountableConnection`

#### `order`

Look up an order by ID or external reference.

**Returns:** `Order`

#### `orderByToken`

Look up an order by token.

**Returns:** `Order`

#### `orderSettings`

Order related settings from site settings. Returns `orderSettings` for the first `channel` in alphabetical order.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `OrderSettings`

#### `ordersTotal`

Return the total sales amount from a specific period.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `TaxedMoney`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
