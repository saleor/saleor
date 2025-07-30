# Gift Cards API

Handle gift card creation, management, and redemption operations.

## Available Operations

This category includes 5 operations:

### Queries

#### `giftCard`

Look up a gift card by ID.
  
  Requires one of the following permissions: MANAGE_GIFT_CARD.

**Returns:** `GiftCard`

#### `giftCardCurrencies`

List of gift card currencies.
  
  Requires one of the following permissions: MANAGE_GIFT_CARD.

**Returns:** `[String!]!`

#### `giftCardSettings`

Gift card related settings from site settings.
  
  Requires one of the following permissions: MANAGE_GIFT_CARD.

**Returns:** `GiftCardSettings!`

#### `giftCardTags`

List of gift card tags.
  
  Requires one of the following permissions: MANAGE_GIFT_CARD.

**Returns:** `GiftCardTagCountableConnection`

#### `giftCards`

List of gift cards.
  
  Requires one of the following permissions: MANAGE_GIFT_CARD.

**Returns:** `GiftCardCountableConnection`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
