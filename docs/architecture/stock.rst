Stock Management
================

Each product variant has a stock keeping unit (SKU).

Each variant holds information about *quantity* at hand, quantity *allocated* for already placed orders and quantity *available*.

**Example:** There are five boxes of shoes. Three of them have already been sold to customers but were not yet dispatched for shipment. The stock records **quantity** is **5**, **quantity allocated** is **3** and **quantity available** is **2**.

Each variant also has a *cost price* (the price that your store had to pay to obtain it).


Product Availability
--------------------

A variant is *in stock* if it has unallocated quantity.

The highest quantity that can be ordered is the available quantity in product variant.


Allocating Stock for New Orders
-------------------------------

Once an order is placed, quantity needed to fulfil each order line is immediately marked as *allocated*.

**Example:** A customer places an order for another box of shoes. The stock records **quantity** is **5**, **quantity allocated** is now **4** and **quantity available** becomes **1**.


Decreasing Stock After Shipment
-------------------------------

Once order lines are marked as shipped, each corresponding stock record will have both its quantity at hand and quantity allocated decreased by the number of items shipped.

**Example:** Two boxes of shoes from warehouse A are shipped to a customer. The stock records **quantity** is now **3**, **quantity allocated** becomes **2** and **quantity available** stays at **1**.
