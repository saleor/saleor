Search engine optimization (SEO)
================================

Out of the box Saleor will automatically handle certain aspects of how search engines see and index your products.

Sitemaps
--------

A special resource reachable under the ``/sitemap.xml`` URL serves an up to date list of products and categories from your site in an easy to parse Sitemaps XML format understood by all major search engines.


Meta tags
---------

Meta keywords are not used as they are ignored by all major search engines because of the abuse this feature saw in the years since it was introduced.

Meta description will be set to the product's description field. This does not affect the search engine ranking but it affects the snippet of text shown along with the search result.

JSON-LD
-------

All product pages contain semantic descriptions in JSON-LD `Structured Data <https://developers.google.com/search/docs/guides/intro-structured-data>`_ format.

It does not directly affect the search engine ranking but it allows search engines to better understand the data ("this is a product, it's available, it costs $10").

It allows search engines like Google to show product photos, prices, ratings etc. along with their search results.

Google for Retail
-----------------

Saleor provides product feeds compatible with Google Merchant Center.

It's available under the ``/feeds/google/`` URL.

As generating this feed is quite costly, there is a separate management command responsible for generating the necessary files:

.. code-block:: bash

 $ python manage.py update_feeds
