# coding=utf-8

from __future__ import unicode_literals

import inspect

from .compat import getargspec

from faker import utils


class Documentor(object):

    def __init__(self, generator):
        """
        :param generator: a localized Generator with providers filled,
                          for which to write the documentation
        :type generator: faker.Generator()
        """
        self.generator = generator
        self.max_name_len = 0
        self.already_generated = []

    def get_formatters(self, locale=None, excludes=None, **kwargs):

        self.max_name_len = 0
        self.already_generated = [] if excludes is None else excludes[:]
        formatters = []
        providers = self.generator.get_providers()
        for provider in providers[::-1]:  # reverse
            if locale and provider.__lang__ != locale:
                continue
            formatters.append(
                (provider, self.get_provider_formatters(provider, **kwargs)),
            )
        return formatters

    def get_provider_formatters(self, provider, prefix='fake.',
                                with_args=True, with_defaults=True):

        formatters = {}

        for name, method in inspect.getmembers(provider, inspect.ismethod):
            # skip 'private' method and inherited methods
            if name.startswith('_') or name in self.already_generated:
                continue

            arguments = []
            faker_args = []
            faker_kwargs = {}

            if name == 'binary':
                faker_kwargs['length'] = 1024

            if with_args:
                # retrieve all parameter
                argspec = getargspec(method)

                lst = [x for x in argspec.args if x not in ['self', 'cls']]
                for i, arg in enumerate(lst):

                    if argspec.defaults and with_defaults:

                        try:
                            default = argspec.defaults[i]
                            if utils.is_string(default):
                                default = utils.quote(default)
                            else:
                                # TODO check default type
                                default = "{0}".format(default)

                            arg = "{0}={1}".format(arg, default)

                        except IndexError:
                            pass

                    arguments.append(arg)
                    if with_args == 'first':
                        break

                if with_args != 'first':
                    if argspec.varargs:
                        arguments.append('*' + argspec.varargs)
                    if argspec.varkw:
                        arguments.append('**' + argspec.varkw)

            # build fake method signature
            signature = "{0}{1}({2})".format(prefix,
                                             name,
                                             ", ".join(arguments))

            # make a fake example
            example = self.generator.format(name, *faker_args, **faker_kwargs)

            formatters[signature] = example

            self.max_name_len = max(self.max_name_len, len(signature))
            self.already_generated.append(name)

        return formatters

    @staticmethod
    def get_provider_name(provider_class):
        return provider_class.__provider__
