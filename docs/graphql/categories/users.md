# Users API

Manage customer accounts, staff users, and user-related operations.

## Available Operations

This category includes 7 operations:

### Queries

#### `address`

Look up an address by ID.
  
  Requires one of the following permissions: MANAGE_USERS, OWNER.

**Returns:** `Address`

#### `addressValidationRules`

Returns address validation rules.

**Returns:** `AddressValidationData`

#### `me`

Return the currently authenticated user.

**Returns:** `User`

#### `permissionGroup`

Look up permission group by ID.
  
  Requires one of the following permissions: MANAGE_STAFF.

**Returns:** `Group`

#### `permissionGroups`

List of permission groups.
  
  Requires one of the following permissions: MANAGE_STAFF.

**Returns:** `GroupCountableConnection`

#### `staffUsers`

List of the shop's staff users.
  
  Requires one of the following permissions: MANAGE_STAFF.

**Returns:** `UserCountableConnection`

#### `user`

Look up a user by ID or email address.
  
  Requires one of the following permissions: MANAGE_STAFF, MANAGE_USERS, MANAGE_ORDERS.

**Returns:** `User`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
