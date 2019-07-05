Taxes
=====

Saleor gives a possibility to configure taxes. It supports external tax provides: ``Avarala``, ``Vatlayer``. Currently only one provider can be enabled at the same time.

Configuring taxes
-----------------

There are three ways in which you can configure taxes:

#. All products prices are entered with tax included

   If selected, all prices entered and displayed in dashboard will be treated as gross prices. For example: product with entered price 4.00 € and 19% VAT will have net price calculated to 3.36 € (rounded).

#. Show gross prices to customers in the storefront

   If selected, prices displayed for customers in storefront will be gross (only ``Vatlayer``). Taxes will be properly calculated at checkout. Changing this setting has no effect on displaying orders placed in the past.

#. Charge taxes on shipping rates

   If selected, standard tax rate will be charged on shipping price.

Vatlayer
--------

Configuration can be done in dashboard ``Taxes`` tab.

Taxes are charged according to the rates applicable in the country to which the order is delivered. If tax rate set for the product is not available, standard tax rate is used by default.

Vatlayer handles taxes only in European Union.


Tax rates preview
^^^^^^^^^^^^^^^^^

You can preview tax rates in dashboard ``Taxes`` tab. It lists all countries taxes are handled for. You can see all available tax rates for each country in its details view.


Fetching taxes
^^^^^^^^^^^^^^

  Assuming you have provided a valid ``VATLAYER_ACCESS_KEY``, taxes can be fetched via following command:

  .. code-block:: console

    $ python manage.py get_vat_rates


  If you do not have a VatLayer API key, you can get one by `subscribing for free here <https://vatlayer.com/signup?plan=9>`_.


  .. warning::

    By default, Saleor is making requests to the VatLayer API through HTTP (insecure),
    if you are using a paid VatLayer subscription, you may want to set the settings ``VATLAYER_USE_HTTPS`` to ``True``.


Avalara
-------

All configuration and account setup should be done on the Avalara's admin panel. Saleor uses standard Avalata's  API to fetch tax codes, calculate taxes during the checkout process and transfer data directly to the Avalara's system.

Configuration
^^^^^^^^^^^^^

Only basic data needs to be provided on Saleor side. You need to fill up variables:
``AVATAX_USERNAME_OR_ACCOUNT``, ``AVATAX_PASSWORD_OR_LICENSE``, ``AVATAX_USE_SANDBOX``, ``AVATAX_COMPANY_NAME``, ``AVATAX_AUTOCOMMIT``, (:ref:`see description of variables.<tax_environment_variables>`)


Avalara requires a company address to properly calculate taxes.
The address must be assigned in the dashboard's general section.

.. warning::
  Avalara will not work without company address provided in the dashboard.


Tax codes
^^^^^^^^^
Avalara has own system for classification of product type and expected taxes. On Saleor side, store owner needs to assign Avalara's tax code to the given product type or product itself. If you skip this step, Saleor will use common code for all products (which is not recommended).
Assigning a tax code can be done from dashboard in product type or product section. Both of these sections have a field for assigning tax code for enabled tax gateway.
