Saleor Pages
===================


Setting up custom pages
-----------------------

You can set up your own pages such as "About us" or "Important Announcement!" in the Pages menu in dashboard.
Note that if you are not an admin, you need to be in group with proper permissions.


Providing an URL to your page in storefront
-------------------------------------------

If you want to add a link to recently created page in storefront, all you need to do is to put the following code:

.. code-block:: html

  <a href="{% url "page:details" slug="your-slug" %}">Text for the link</a>

in the proper template.
For example in default Saleor setup, in the footer there is a list of categories:

.. code-block:: html

  {% for category in categories %}
    <li>
      <a href="{{ category.get_absolute_url }}">
        {{ category|capfirst }}
      </a>
    </li>
  {% endfor %}

Say, you want to add "Terms of Service" page with `terms-of-service` slug; you just need to add:

.. code-block:: html

  {% endfor %}
  <li>
    <a href="{% url "page:details" slug="terms-of-service" %}">ToS</a>
  </li>
