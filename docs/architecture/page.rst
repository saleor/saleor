.. _pages-architecture:

Pages
=====


Setting up custom pages
-----------------------

You can set up pages such as "About us" or "Important Announcement!" in the Pages menu in dashboard.
Note that if you are not an admin, you need to be in group with proper permissions.


Default Pages
-------------

There are a few default pages that are created during the migration process (unless otherwise specified).

Some of them are flagged as protected, which means that you cannot delete them or rename their slugs
as they are required by some other parts of Saleor.

Here is the list of automatically generated pages:


.. table::
  :widths: grid

  +------------------+------------------+----------------------+---------------------------------------------------------------------+
  | Page Name        | Protected?       | Slug                 | Description                                                         |
  +==================+==================+======================+=====================================================================+
  | Privacy Policy   | **Yes**          | ``privacy-policy``   | This page contains your, and, thus, the default contract about how  |
  |                  |                  |                      | your store, handle, share, send data sent by your customers.        |
  |                  |                  |                      |                                                                     |
  |                  |                  |                      | This page is required by the Privacy Law of most countries.         |
  |                  |                  |                      |                                                                     |
  +------------------+------------------+----------------------+---------------------------------------------------------------------+
  | Selling Contract | **Yes**          | ``selling-contract`` | This page contains your, sales agreement of your store which        |
  |                  |                  |                      | is required by most countries to collect and get an exchange        |
  |                  |                  |                      | of consent before buying to protect both you and your customer      |
  |                  |                  |                      | from conflicts and accidents.                                       |
  |                  |                  |                      |                                                                     |
  +------------------+------------------+----------------------+---------------------------------------------------------------------+
  | About Us         | No               | ``selling-contract`` | This page contains some miscellaneous information about your store. |
  |                  |                  |                      |                                                                     |
  |                  |                  |                      | *Note: page generated on populate db.*                              |
  |                  |                  |                      |                                                                     |
  +------------------+------------------+----------------------+---------------------------------------------------------------------+


.. note::

  See :ref:`protected-pages-customization` for more information about protected pages.


Referencing pages in storefront
-------------------------------

If you want to add a link to recently created page in storefront, all you need to do is to put the following code:

.. code-block:: html

  <a href="{% url "page:details" slug="terms-of-service" %}">Terms of Service</a>


in the proper template.
