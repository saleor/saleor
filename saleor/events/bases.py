from django.core.exceptions import ImproperlyConfigured
from django.db import models


class EventManager:
    def __init_subclass__(cls, **_options):
        meta = getattr(cls, "Meta", None)
        if not meta or not meta.model:
            raise ImproperlyConfigured('Missing meta model')
        cls._meta = meta

    def __init__(self):
        self.instances = []

    @property
    def base_type(self) -> models.Model:
        return self._meta.model

    @property
    def last(self):
        return self.instances[-1]

    def new_event(self, **data):
        instance = self.base_type(**data)
        self.instances.append(instance)
        return self

    def _commit(self):
        if len(self.instances) == 1:
            return self.instances[0].save()
        return self.base_type.objects.bulk_create(self.instances)

    def save(self):
        if not self.instances:
            return None
        return self._commit()
