# Taxes API

Configure tax rates, tax classes, and tax calculation settings.

## Available Operations

This category includes 11 operations:

### Queries

#### `taxClass`

Look up a tax class.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.

**Returns:** `TaxClass`

#### `taxClasses`

List of tax classes.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.

**Returns:** `TaxClassCountableConnection`

#### `taxConfiguration`

Look up a tax configuration.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.

**Returns:** `TaxConfiguration`

#### `taxConfigurations`

List of tax configurations.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.

**Returns:** `TaxConfigurationCountableConnection`

#### `taxCountryConfiguration`

Tax class rates grouped by country.
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.

**Returns:** `TaxCountryConfiguration`

#### `taxCountryConfigurations`

#### `taxTypes`

List of all tax rates available from tax gateway.

**Returns:** `[TaxType!]`

### Mutations

#### `taxClassCreate`

Create a tax class. 
  
  Requires one of the following permissions: MANAGE_TAXES.

**Returns:** `TaxClassCreate`

#### `taxClassDelete`

Delete a tax class. After deleting the tax class any products, product types or shipping methods using it are updated to use the default tax class. 
  
  Requires one of the following permissions: MANAGE_TAXES.

**Returns:** `TaxClassDelete`

#### `taxClassUpdate`

Update a tax class. 
  
  Requires one of the following permissions: MANAGE_TAXES.

**Returns:** `TaxClassUpdate`

#### `taxConfigurationUpdate`

Update tax configuration for a channel. 
  
  Requires one of the following permissions: MANAGE_TAXES.

**Returns:** `TaxConfigurationUpdate`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
