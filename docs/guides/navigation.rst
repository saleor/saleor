Navigation
==========

Saleor gives a possibility to configure storefront navigation. It can be done in dashboard ``Navigation`` tab.

You can add up to 3 levels of menu items inside every menu you create. Each menu item can point to an internal page with Category, Collection, Page or an external website by passing an extra URL.


Managing menu items
-------------------

To manage menu items, first you must go to dashboard ``Navigation`` tab and choose menu to edit. If you want to manage nested menu items, you can navigate through listed menu items up and down.

To add new menu item, choose ``Add`` button visible above the list of menu items. Then fill up the form and click ``Create``.

To edit menu item, choose ``Edit`` button visible next to a menu item on the list or ``Edit menu item`` button below menu item details, if you're inside menu item details view. Make any changes and click ``Update``.

To remove a menu item, choose ``Remove`` button visible next to a menu item on the list or ``Remove menu item`` button below menu item details, if you're inside menu item details view. This action will remove all descendant items and can't be undone.

The menu items display on the storefront in the order that they are listed in menu items list. You can reorder them by handling an icon on the left to the menu items and dragging them to another position.


Managing menus
--------------

Dashboard gives you a possibility to add new menus.

There can be two active menus at once (one for the navbar, the other one for the footer, they can be the same).

Currently assigned menus can be changed via dashboard's ``Navigation`` panel.

Menu is rendered as a vertical list by default. You can change it by passing an extra ``horizontal=True`` argument. Horizontal menus with nested items appear as a dropdown menu on desktops.
