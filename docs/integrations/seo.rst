Search Engine Optimization (SEO)
================================

Out of the box Saleor will automatically handle certain aspects of how search engines see and index your products.

Sitemaps
--------

A special resource reachable under the ``/sitemap.xml`` URL serves an up to date list of products, categories and collections from your site in an easy to parse Sitemaps XML format understood by all major search engines.


Meta Tags
---------

Meta keywords are not used as they are ignored by all major search engines because of the abuse this feature saw in the years since it was introduced.

Meta description will be set to the product's description field. This does not affect the search engine ranking but it affects the snippet of text shown along with the search result.


Robots Meta Tag
---------------

The robots meta tag utilize a page-specific approach to controlling how an individual page should be indexed and served to users in search results.

We've restricted Dashboard Admin Panel from crawling and indexation, content-less pages (eg. cart, sign up, login) are not crawled.


Structured Data
---------------

Homepage and product pages contain semantic descriptions in JSON-LD `Structured Data <https://developers.google.com/search/docs/guides/intro-structured-data>`_ format.

It does not directly affect the search engine ranking but it allows search engines to better understand the data ("this is a product, it's available, it costs $10").

It allows search engines like Google to show product photos, prices, availability, ratings etc. along with their search results.


Nofollow links
--------------

Search engine crawlers can’t sign in or register as a member on your site, no reason to invite them to follow “register here” or “sign in” links, as there will be little to none valuable content.

This will optimize time spent by the crawler on the website, giving it time it to index more content-related pages.
