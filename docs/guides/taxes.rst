Taxes
=====

Saleor gives a possibility to configure taxes. It can be done in dashboard ``Taxes`` tab.

Taxes are charged according to the rates applicable in the country to which the order is delivered. If tax rate set for the product is not available, standard tax rate is used by default.

For now, only taxes in European Union are handled.


Configuring taxes
-----------------

There are three ways in which you can configure taxes:

#. All products prices are entered with tax included

   If selected, all prices entered and displayed in dashboard will be treated as gross prices. For example: product with entered price 4.00 € and 19% VAT will have net price calculated to 3.36 € (rounded).

#. Show gross prices to customers in the storefront

   If selected, prices displayed for customers in storefront will be gross. Taxes will be properly calculated at checkout. Changing this setting has no effect on displaying orders placed in the past.

#. Charge taxes on shipping rates

   If selected, standard tax rate will be charged on shipping price.


Tax rates preview
-----------------

You can preview tax rates in dashboard ``Taxes`` tab. It lists all countries taxes are handled for. You can see all available tax rates for each country in its details view.


Fetching taxes
--------------

  Assuming one provided valid ``VATLAYER_ACCESS_KEY``, taxes can be fetched via following command:

  .. code-block:: console

  $ python manage.py get_vat_rates
