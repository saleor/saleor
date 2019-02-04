Shippings
=========

Saleor uses the concept of Shipping Zones and Shipping Methods to fulfill the shipping process.

Shipping Zones
--------------

The countries that you ship to are known as the shipping zones. Each ``ShippingZone`` includes ``ShippingMethods`` that apply to customers whose shipping address is within the shipping zone.

Each ``ShippingZone`` can contain several countries inside, but the country might belong to a maximum of one ``ShippingZone``.

Some examples of the ``ShippingZones`` could be `European Union`, `North America`, `Germany` etc.

There's also a possibility to create a default Shipping Zone which will be used for countries not covered by other zones.

Shipping Methods
----------------

``ShippingMethods`` are the methods you'll use to get customers' orders to them.
You can offer several ones within one ``ShippingZone`` to ensure the varieties of delivery speed and costs at the checkout.

Each ``ShippmentMethod`` could be one of the two types:

- ``PRICE_BASED``
    Those methods can be used only when the order price is within the certain range, eg. from 0 to 50$, 50$ and up etc.

- ``WEGHT_BASED``
    Same as the ``PRICE_BASED``, but with the total order's weight in mind.

These methods allow you to cover most of the basic use cases, eg.

- Listing several methods with different prices and shipping time for different countries.

- Offering a free (or discounted) shipping on orders above certain price threshold.

- Increasing the shipping price for heavy orders.

Weight
------

Weight is used to calculate the ``WEIGHT_BASED`` shipping price.

Weight is defined on the ``ProductType`` level and can be overridden
for each ``Product`` and each ``ProductVariant`` within a ``Product``.
