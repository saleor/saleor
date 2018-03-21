Thumbnails
==========

Saleor uses `VersatileImageField <https://github.com/respondcreate/django-versatileimagefield>`_ replacement for Django's ImageField.



Generating Products Thumbnails Manually
-----------------------------------------

Create missing thumbnails for all ProductImage instances.

.. code-block:: console

 $ python manage.py create_thumbnails


Deleting Image Renditions
--------------------------

Image renditions are not deleted automatically with the main image, however Saleor handles that on ``post_delete`` model's signal.
More on deleting rendition images can be found in `VersatileImageField documentation <https://django-versatileimagefield.readthedocs.io/en/latest/deleting_created_images.html>`_
