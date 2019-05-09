from django.apps import AppConfig


class VersatileImageFieldConfig(AppConfig):
    """The Django app config for django-versatileimagefield."""
    name = 'versatileimagefield'
    verbose_name = "VersatileImageField"

    def ready(self):
        from .registry import autodiscover
        autodiscover()
