Stock Management
================

Each product variant has a stock keeping unit (SKU) and can have any number of stock records.

A stock record represents that variant's availability in a single location. Multiple stock records are often used to represent different warehouses, different fulfilment partners or separate shipments of the same product that were obtained at different prices.

Each stock record holds information about *quantity* at hand, quantity *allocated* for already placed orders and quantity *available*.

**Example:** There are five boxes of shoes in warehouse A. Three of them have already been sold to customers but were not yet dispatched for shipment. The stock records **quantity** is **5**, **quantity allocated** is **3** and **quantity available** is **2**.

Each stock records also has a *cost price* (the price that your store had to pay to obtain it).


Product Availability
--------------------

A variant is *in stock* if at least one of its stock records has unallocated quantity.

The highest quantity that can be ordered is the sum of all available quantities in stock records. It allows each ordered product to be fulfilled in multiple order lines with all stock records.


Allocating Stock for New Orders
-------------------------------

Once an order is placed, a stock records are selected to fulfil each order line. Default logic will select the stock records with the *lowest cost price* that holds enough stock. Quantity needed to fulfil the order line is immediately marked as *allocated*.

**Example:** A customer places an order for another box of shoes and warehouse A is selected to fulfil the order. The stock records **quantity** is **5**, **quantity allocated** is now **4** and **quantity available** becomes **1**.


Decreasing Stock After Shipment
-------------------------------

Once a delivery group is marked as shipped, each stock record used to fulfil its lines will have both its quantity at hand and quantity allocated decreased by the number of items shipped.

**Example:** Two boxes of shoes from warehouse A are shipped to a customer. The stock records **quantity** is now **3**, **quantity allocated** becomes **2** and **quantity available** stays at **1**.
