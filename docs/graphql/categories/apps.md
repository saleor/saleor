# Apps API

Manage third-party applications and app integrations.

## Available Operations

This category includes 5 operations:

### Queries

#### `app`

Look up an app by ID. If ID is not provided, return the currently authenticated app.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER AUTHENTICATED_APP. The authenticated app has access to its resources. Fetching different apps requires MANAGE_APPS permission.

**Returns:** `App`

#### `appExtension`

Look up an app extension by ID.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.

**Returns:** `AppExtension`

#### `appExtensions`

List of all extensions.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.

**Returns:** `AppExtensionCountableConnection`

#### `apps`

List of the apps.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, MANAGE_APPS.

**Returns:** `AppCountableConnection`

#### `appsInstallations`

List of all apps installations
  
  Requires one of the following permissions: MANAGE_APPS.

**Returns:** `[AppInstallation!]!`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
