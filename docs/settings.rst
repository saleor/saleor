SiteSettings
============

SiteSettings module allows your users to change common shop settings from dashboard.
Settings object is chosen by pk from ``SITE_SETTINGS_ID`` variable.


Context processor
-----------------
Thanks to ``saleor.site.context_processors.settings`` you can access SiteSettings in template with ``settings`` variable.

.. code-block:: html

    <!-- saleor/templates/dashboard/sites/detail.html -->
    <div class="row">
        <p>
            {{ settings.header_text }}
        </p>
    </div>


New fields
----------
To add new settings variable you must modify SiteSettings model:

.. code-block:: python

    # saleor/site/models.py
    @python_2_unicode_compatible
    class SiteSettings(models.Model):
        domain = models.CharField(
            pgettext_lazy('Site field', 'domain'), max_length=100,
            validators=[_simple_domain_name_validator], unique=True)

        name = models.CharField(pgettext_lazy('Site field', 'name'), max_length=50)
        header_text = models.CharField(pgettext_lazy('Site field', 'header text'),
                                       max_length=200, blank=True)
        # new field
        welcome_message = models.TextField(pgettext_lazy('Site field', 'welcome message'),
                                           blank=True)


And dashboard form:

.. code-block:: html

    <!-- saleor/templates/dashboard/sites/detail.html -->
    {% block content %}
        <form method="post" id="form-category" enctype="multipart/form-data" novalidate>
            {% csrf_token %}
            <div class="row">
                <div class="col l8">
                    <div class="row">
                        {{ form.name|materializecss }}
                        {{ form.domain|materializecss }}
                        {{ form.header_text|materializecss }}
                        <!-- new field: -->
                        {{ form.welcome_message|materializecss }}
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col s12 l8 right-align">
                      <button type="submit" class="btn">{% trans "Update" %}</button>
                </div>
            </div>
        </form>
    {% endblock %}

After database migration you will be able to change ``welcome_message``.
