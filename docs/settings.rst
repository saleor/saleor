SiteSettings
============

SiteSettings module allows your users to change common shop settings from dashboard like its name or domain.
Settings object is chosen by pk from ``SITE_SETTINGS_ID`` variable.


Context processor
-----------------
Thanks to ``saleor.site.context_processors.settings`` you can access SiteSettings in template with ``settings`` variable.
