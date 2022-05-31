from django.apps import AppConfig


class CustomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'custom'
