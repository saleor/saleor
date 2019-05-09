import sys

import six

from django.core.exceptions import ImproperlyConfigured

from .utils import import_attribute


class AppConfOptions(object):

    def __init__(self, meta, prefix=None):
        self.prefix = prefix
        self.holder_path = getattr(meta, 'holder', 'django.conf.settings')
        self.holder = import_attribute(self.holder_path)
        self.proxy = getattr(meta, 'proxy', False)
        self.required = getattr(meta, 'required', [])
        self.configured_data = {}

    def prefixed_name(self, name):
        if name.startswith(self.prefix.upper()):
            return name
        return "%s_%s" % (self.prefix.upper(), name.upper())

    def contribute_to_class(self, cls, name):
        cls._meta = self
        self.names = {}
        self.defaults = {}


class AppConfMetaClass(type):

    def __new__(cls, name, bases, attrs):
        super_new = super(AppConfMetaClass, cls).__new__
        parents = [b for b in bases if isinstance(b, AppConfMetaClass)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        attr_meta = attrs.pop('Meta', None)
        if attr_meta:
            meta = attr_meta
        else:
            attr_meta = type('Meta', (object,), {})
            meta = getattr(new_class, 'Meta', None)

        prefix = getattr(meta, 'prefix', getattr(meta, 'app_label', None))
        if prefix is None:
            # Figure out the prefix by looking one level up.
            # For 'django.contrib.sites.models', this would be 'sites'.
            model_module = sys.modules[new_class.__module__]
            prefix = model_module.__name__.split('.')[-2]

        new_class.add_to_class('_meta', AppConfOptions(meta, prefix))
        new_class.add_to_class('Meta', attr_meta)

        for parent in parents[::-1]:
            if hasattr(parent, '_meta'):
                new_class._meta.names.update(parent._meta.names)
                new_class._meta.defaults.update(parent._meta.defaults)
                new_class._meta.configured_data.update(
                    parent._meta.configured_data)

        for name in filter(str.isupper, list(attrs.keys())):
            prefixed_name = new_class._meta.prefixed_name(name)
            new_class._meta.names[name] = prefixed_name
            new_class._meta.defaults[prefixed_name] = attrs.pop(name)

        # Add all attributes to the class.
        for name, value in attrs.items():
            new_class.add_to_class(name, value)

        new_class._configure()
        for name, value in six.iteritems(new_class._meta.configured_data):
            prefixed_name = new_class._meta.prefixed_name(name)
            setattr(new_class._meta.holder, prefixed_name, value)
            new_class.add_to_class(name, value)

        # Confirm presence of required settings.
        for name in new_class._meta.required:
            prefixed_name = new_class._meta.prefixed_name(name)
            if not hasattr(new_class._meta.holder, prefixed_name):
                raise ImproperlyConfigured('The required setting %s is'
                                           ' missing.' % prefixed_name)

        return new_class

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def _configure(cls):
        # the ad-hoc settings class instance used to configure each value
        obj = cls()
        for name, prefixed_name in six.iteritems(obj._meta.names):
            default_value = obj._meta.defaults.get(prefixed_name)
            value = getattr(obj._meta.holder, prefixed_name, default_value)
            callback = getattr(obj, "configure_%s" % name.lower(), None)
            if callable(callback):
                value = callback(value)
            cls._meta.configured_data[name] = value
        cls._meta.configured_data = obj.configure()


class AppConf(six.with_metaclass(AppConfMetaClass)):
    """
    An app setting object to be used for handling app setting defaults
    gracefully and providing a nice API for them.
    """
    def __init__(self, **kwargs):
        for name, value in six.iteritems(kwargs):
            setattr(self, name, value)

    def __dir__(self):
        return sorted(set(self._meta.names.keys()))

    # For instance access..
    @property
    def configured_data(self):
        return self._meta.configured_data

    def __getattr__(self, name):
        if self._meta.proxy:
            return getattr(self._meta.holder, name)
        raise AttributeError("%s not found. Use '%s' instead." %
                             (name, self._meta.holder_path))

    def __setattr__(self, name, value):
        if name == name.upper():
            setattr(self._meta.holder,
                    self._meta.prefixed_name(name), value)
        object.__setattr__(self, name, value)

    def configure(self):
        """
        Hook for doing any extra configuration, returning a dictionary
        containing the configured data.
        """
        return self.configured_data
