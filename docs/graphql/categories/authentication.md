# Authentication API

Handle user authentication, tokens, and permission management.

## Available Operations

This category includes 19 operations:

### Mutations

#### `externalAuthenticationUrl`

Prepare external authentication URL for user by custom plugin.

**Returns:** `ExternalAuthenticationUrl`

#### `externalLogout`

Logout user by custom plugin.

**Returns:** `ExternalLogout`

#### `externalObtainAccessTokens`

Obtain external access tokens for user by custom plugin.

**Returns:** `ExternalObtainAccessTokens`

#### `externalRefresh`

Refresh user's access by custom plugin.

**Returns:** `ExternalRefresh`

#### `externalVerify`

Verify external authentication data by plugin.

**Returns:** `ExternalVerify`

#### `field`

Sort attempts by the selected field.

**Returns:** `EventDeliveryAttemptSortField!`

#### `permissions`

List of the app's permissions.

**Returns:** `[Permission!]`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `reason`

Explanation for the applied discount.
  
  Requires one of the following permissions: MANAGE_ORDERS.

**Returns:** `String`

#### `tokenCreate`

Create JWT token.

**Returns:** `CreateToken`

#### `tokenRefresh`

Refresh JWT token. Mutation tries to take refreshToken from the input. If it fails it will try to take `refreshToken` from the http-only cookie `refreshToken`. `csrfToken` is required when `refreshToken` is provided as a cookie.

**Returns:** `RefreshToken`

#### `tokenVerify`

Verify JWT token.

**Returns:** `VerifyToken`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
