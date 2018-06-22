.. _money_architecture:


Handling Money Amounts
======================

Saleor uses the `Prices <https://github.com/mirumee/prices/>`_ and `django-prices <https://github.com/mirumee/django-prices/>`_ libraries to store, calculate and display amounts of money, prices and ranges of those and `django-prices-vatlayer <https://github.com/mirumee/django-prices-vatlayer>`_ to handle VAT tax rates in European Union (optionally).


Default currency
----------------

All prices are entered and stored in a single default currency controlled by the :ref:`DEFAULT_CURRENCY <settings_configuration>` settings key. Saleor can display prices in a user's local currency (see :ref:`openexchangerates`) but all purchases are charged in the default currency.

.. warning::

  The currency is not stored in the database. Changing the default currency in a production environment will not recalculate any existing orders. All numbers will remain the same and will be incorrectly displayed as the new currency.


Money and TaxedMoney
--------------------

In Saleor's codebase, money amounts exist either as `Money` or `TaxedMoney` instances.

`Money` is a type representing amount of money in specific currency: 100 USD is represented by `Money(100, 'USD')`.
This type doesn't hold any additional information useful for commerce but, unlike `Decimal`, it implements safeguards and checks for calculations and comparisons of monetary values.

Money amounts are stored on model using `MoneyField` that provides its own safechecks on currency and precision of stored amount.

If you ever need to get to the `Decimal` of your `Money` object, you'll find it on the `amount` property.

Products and shipping methods prices are stored using `MoneyField`. All prices displayed in dashboard, excluding orders, are as they have been entered in the forms. You can decide if those prices are treated as gross or net in dashboard ``Taxes`` tab.

Prices displayed in orders are gross or net depending on setting how prices are displayed for customers, both in storefront and dashboard. This way staff users will always see the same state of an order as the customer.


TaxedMoneyRange
---------------

Sometimes a product may be available under more than single price due to its variants defining custom prices different from the base price.

For such situations `Product` defines additional `get_price_range` method that return `TaxedMoneyRange` object defining minimum and maximum prices on its `start` and `stop` attributes.
This object is then used by the UI to differentiate between displaying price as "10 USD" or "from 10 USD" in case of products where prices differ between variants.
