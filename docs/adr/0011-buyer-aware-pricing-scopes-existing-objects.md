# Buyer-aware pricing scopes existing objects instead of adding a price list

**Tags:** pricing, discounts, customer types, graphql

A merchant can give different buyers a different base price for the same variant in a channel
through scoped prices on the variant channel listing, and can limit a promotion rule to a set of
buyers through conditions on the rule. Both use the same vocabulary: customer types and values of
customer attributes, matched as one listed value per dimension is enough and every declared
dimension must hold. There is no price list entity and no buyer group entity.

The alternative, a price list that a customer type points to, would have duplicated the catalogue
per buyer segment and forced the merchant to maintain the same product in several places. Scoping
the price on the listing keeps one product with one default price, so a store that never creates a
scoped price is unaffected, and a scoped price is removed by deleting one row. The scope reuses the
customer types and customer attributes that already segment users, so the dashboard screens that
manage them are reused as well.

## What the API freezes

- `ProductVariantChannelListing.prices` lists the scoped prices of a listing. A price carries its
  customer types, its customer attribute conditions grouped per attribute, and a validity window.
  Three mutations create, update and delete one price. There is no bulk mutation, a client aliases
  the single ones in a request, and a bulk one can be added later without breaking anything.
- `PromotionRule.customerTypes` and `PromotionRule.customerAttributes` carry the same conditions on
  a rule, written through `customerTypes` and `customerAttributeValues` on the rule inputs. The
  conditions are rule fields, not a branch of the predicate tree, so a rule can be scoped to buyers
  without the predicate language growing a buyer vocabulary.
- Inputs take flat lists of value ids and outputs group the values per attribute, because an
  attribute value does not expose its attribute, and a client rendering a condition needs both.
- The `customer` argument on the pricing fields previews prices as a given customer and requires
  both `MANAGE_PRODUCTS` and `MANAGE_USERS`, since it reveals what a customer would pay.
- Deleting a customer type, an attribute or a value that a scoped price or a rule references is
  refused with `CANNOT_DELETE` and the counts of the referencing objects, so a deletion cannot
  silently widen a price or a promotion.

## Resolution rules the schema relies on

- A custom line price beats a scoped price, which beats the listing price. Among scoped prices the
  one matching the most dimensions wins, then the lowest price.
- Guests have no customer type and never match a buyer condition. A logged in user without a type
  is a member of the default type.
- A value counts only while its attribute is assigned to the buyer's customer type.
- The best single promotion rule wins for a buyer, as it does for a guest. Rules do not stack.
- The stored discounted price of a listing stays the guest price. Catalogue sorting and the price
  filter read it, so they do not reflect a buyer's scoped price or a buyer-conditioned rule.
- A price with only a validity window applies to everyone, guests included, and is folded into the
  stored price while the window is open, with up to about a minute of lag after it closes.

## Known gaps accepted at the freeze

- The API does not list which products or promotions reference a customer type or a value. The
  counts in the refused deletion are the only signal. A filter is additive and can be added when a
  client needs it.
- A listing holds at most 100 scoped prices and a condition lists at most 100 items.
