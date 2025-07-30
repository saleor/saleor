# Products API

Manage product catalog, variants, types, and inventory operations.

## Available Operations

This category includes 20 operations:

### Queries

#### `categories`

List of the shop's categories.

**Returns:** `CategoryCountableConnection`

#### `category`

Name of the grouping category

**Returns:** `String!`

#### `collection`

Look up a collection by ID or slug. If slugLanguageCode is provided, category will be fetched by slug translation. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS.

**Returns:** `Collection`

#### `collections`

List of the shop's collections. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS.

**Returns:** `CollectionCountableConnection`

#### `digitalContent`

Look up digital content by ID.
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `DigitalContent`

#### `digitalContents`

List of digital content.
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `DigitalContentCountableConnection`

#### `product`

Look up a product by ID. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS.

**Returns:** `Product`

#### `productType`

Look up a product type by ID.

**Returns:** `ProductType`

#### `productTypes`

List of the shop's product types.

**Returns:** `ProductTypeCountableConnection`

#### `productVariant`

Look up a product variant by ID or SKU. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS.

**Returns:** `ProductVariant`

#### `reportProductSales`

List of top selling products.
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `ProductVariantCountableConnection`

#### `stock`

Look up a stock by ID
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `Stock`

#### `stocks`

List of stocks.
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `StockCountableConnection`

#### `warehouse`

Look up a warehouse by ID.
  
  Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS, MANAGE_SHIPPING.

**Returns:** `Warehouse`

#### `warehouses`

List of warehouses.
  
  Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS, MANAGE_SHIPPING.

**Returns:** `WarehouseCountableConnection`

### Mutations

#### `assignWarehouseShippingZone`

Add shipping zone to given warehouse. 
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `WarehouseShippingZoneAssign`

#### `createWarehouse`

Creates new warehouse. 
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `WarehouseCreate`

#### `deleteWarehouse`

Deletes selected warehouse. 
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `WarehouseDelete`

#### `unassignWarehouseShippingZone`

Remove shipping zone from given warehouse. 
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `WarehouseShippingZoneUnassign`

#### `updateWarehouse`

Updates given warehouse. 
  
  Requires one of the following permissions: MANAGE_PRODUCTS.

**Returns:** `WarehouseUpdate`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
