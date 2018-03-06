Pages
=====


Setting up custom pages
-----------------------

You can set up pages such as "About us" or "Important Announcement!" in the Pages menu in dashboard.
Note that if you are not an admin, you need to be in group with proper permissions.


Referencing pages in storefront
-------------------------------

If you want to add a link to recently created page in storefront, all you need to do is to put the following code:

.. code-block:: html

  <a href="{% url "page:details" slug="terms-of-service" %}">Terms of Service</a>

in the proper template.
