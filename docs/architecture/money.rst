Handling Money Amounts
======================

Saleor uses the `Prices <https://github.com/mirumee/prices/>`_ and `django-prices <https://github.com/mirumee/django-prices/>`_ libraries to store, calculate and display amounts of money, prices and ranges of those.

Default currency
----------------

All prices are entered and stored in a single default currency controlled by the [DEFAULT_CURRENCY setting]. Saleor can display prices in a user's local currency (see [Open Exchange Rates integration]) but all purchases are charged in the default currency.

.. warning::

  The currency is not stored in the database. Changing the default currency in a production environment will not recalculate any existing orders. All numbers will remain the same and will be incorrectly displayed as the new currency.

Money and TaxedMoney
--------------------

In Saleor's codebase, money amounts exist either as `Money` or `TaxedMoney` instances.

`Money` is a type representing amount of money in specific currency: 100 USD is represented by `Money(100, 'USD')`. This type doesn't hold any additional information useful for commerce but, unlike `Decimal`, it implements safeguards and checks for calculations and comparisions of monetary values. Money amounts are stored on model using `MoneyField` that provides its own safechecks on currency and precision of stored amount. If you ever need to get to the `Decimal` of your `Money` object, you'll find it on the `amount` property.

Products and shipping methods prices are stored using `MoneyField` and are assumed to be gross amounts. Those amounts are then naively converted to `TaxedMoney` objects using the `TaxedAmount(net=item.price, gross=item.price)` approach with conversion happening before resolving item's final price (before taxes and discounts).

.. note::
  
  In future Saleor will support setting for store administrators to change this approach to use net values instead if this fits their business more.

TaxedMoneyRange
---------------

Sometimes a product may be available under more than single price due to it's variants defining custom prices different from base brice. For such situations `Product` defines additional `get_price_range` and `get_gross_price_range` methods that return `TaxedMoneyRange` object defining minim and maximum prices on its `start` and `stop` attributes. This object is then used by the UI to differentatie between displaying price as "10 USD" or "from 10 USD" in case of products where prices differ between variants.

TaxedMoneyRange is also used in for displaying other money ranges, like min and maximum cost and margin on product's variant in dashboard.