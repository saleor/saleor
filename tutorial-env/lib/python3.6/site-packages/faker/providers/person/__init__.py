from __future__ import unicode_literals

from .. import BaseProvider


localized = True


class Provider(BaseProvider):
    formats = ['{{first_name}} {{last_name}}']

    first_names = ['John', 'Jane']

    last_names = ['Doe']

    def name(self):
        """
        :example 'John Doe'
        """
        pattern = self.random_element(self.formats)
        return self.generator.parse(pattern)

    def first_name(self):
        return self.random_element(self.first_names)

    def last_name(self):
        return self.random_element(self.last_names)

    def name_male(self):
        if hasattr(self, 'formats_male'):
            formats = self.formats_male
        else:
            formats = self.formats
        pattern = self.random_element(formats)
        return self.generator.parse(pattern)

    def name_female(self):
        if hasattr(self, 'formats_female'):
            formats = self.formats_female
        else:
            formats = self.formats
        pattern = self.random_element(formats)
        return self.generator.parse(pattern)

    def first_name_male(self):
        if hasattr(self, 'first_names_male'):
            return self.random_element(self.first_names_male)
        return self.first_name()

    def first_name_female(self):
        if hasattr(self, 'first_names_female'):
            return self.random_element(self.first_names_female)
        return self.first_name()

    def last_name_male(self):
        if hasattr(self, 'last_names_male'):
            return self.random_element(self.last_names_male)
        return self.last_name()

    def last_name_female(self):
        if hasattr(self, 'last_names_female'):
            return self.random_element(self.last_names_female)
        return self.last_name()

    def prefix(self):
        if hasattr(self, 'prefixes'):
            return self.random_element(self.prefixes)
        if hasattr(self, 'prefixes_male') and hasattr(self, 'prefixes_female'):
            prefixes = self.random_element(
                (self.prefixes_male, self.prefixes_female))
            return self.random_element(prefixes)
        return ''

    def prefix_male(self):
        if hasattr(self, 'prefixes_male'):
            return self.random_element(self.prefixes_male)
        return self.prefix()

    def prefix_female(self):
        if hasattr(self, 'prefixes_female'):
            return self.random_element(self.prefixes_female)
        return self.prefix()

    def suffix(self):
        if hasattr(self, 'suffixes'):
            return self.random_element(self.suffixes)
        if hasattr(self, 'suffixes_male') and hasattr(self, 'suffixes_female'):
            suffixes = self.random_element(
                (self.suffixes_male, self.suffixes_female))
            return self.random_element(suffixes)
        return ''

    def suffix_male(self):
        if hasattr(self, 'suffixes_male'):
            return self.random_element(self.suffixes_male)
        return self.suffix()

    def suffix_female(self):
        if hasattr(self, 'suffixes_female'):
            return self.random_element(self.suffixes_female)
        return self.suffix()
