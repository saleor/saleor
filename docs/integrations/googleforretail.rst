Google for Retail
=================

Saleor has tools for generating product feed which can be used with Google Merchant Center. Final file is compressed CSV and saved in location specified by ``saleor.data_feeds.google_merchant.FILE_PATH`` variable.

To generate feed use command:

.. code-block:: bash

    $ python manage.py update_feeds

It's recommended to run this command periodically.

Merchant Center has few country dependent settings, so please validate your feed at Google dashboard. You can also specify there your shipping cost, which is required feed parameter in many countries. More info be found at `Google Support pages <https://support.google.com/merchants>`_.

One of required by Google fields is *brand* attribute. Feed generator checks for it in variant attribute named *brand* or *publisher* (if not, checks in product).

Feed can be downloaded from url: ``http://<yourserver>/feeds/google/``
