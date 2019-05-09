# coding=utf-8
from __future__ import unicode_literals

from .. import BaseProvider
from .. import date_time

localized = True


class Provider(BaseProvider):
    city_suffixes = ['Ville']
    street_suffixes = ['Street']
    city_formats = ('{{first_name}} {{city_suffix}}', )
    street_name_formats = ('{{last_name}} {{street_suffix}}', )
    street_address_formats = ('{{building_number}} {{street_name}}', )
    address_formats = ('{{street_address}} {{postcode}} {{city}}', )
    building_number_formats = ('##', )
    postcode_formats = ('#####', )
    countries = [tz['name'] for tz in date_time.Provider.countries]

    ALPHA_2 = 'alpha-2'
    ALPHA_3 = 'alpha-3'

    alpha_2_country_codes = [tz['alpha-2-code'] for tz in date_time.Provider.countries]
    alpha_3_country_codes = [tz['alpha-3-code'] for tz in date_time.Provider.countries]

    def city_suffix(self):
        """
        :example 'town'
        """
        return self.random_element(self.city_suffixes)

    def street_suffix(self):
        """
        :example 'Avenue'
        """
        return self.random_element(self.street_suffixes)

    def building_number(self):
        """
        :example '791'
        """
        return self.numerify(self.random_element(self.building_number_formats))

    def city(self):
        """
        :example 'Sashabury'
        """
        pattern = self.random_element(self.city_formats)
        return self.generator.parse(pattern)

    def street_name(self):
        """
        :example 'Crist Parks'
        """
        pattern = self.random_element(self.street_name_formats)
        return self.generator.parse(pattern)

    def street_address(self):
        """
        :example '791 Crist Parks'
        """
        pattern = self.random_element(self.street_address_formats)
        return self.generator.parse(pattern)

    def postcode(self):
        """
        :example 86039-9874
        """
        return self.bothify(self.random_element(self.postcode_formats)).upper()

    def address(self):
        """
        :example '791 Crist Parks, Sashabury, IL 86039-9874'
        """
        pattern = self.random_element(self.address_formats)
        return self.generator.parse(pattern)

    def country(self):
        return self.random_element(self.countries)

    def country_code(self, representation=ALPHA_2):
        if representation == self.ALPHA_2:
            return self.random_element(self.alpha_2_country_codes)
        elif representation == self.ALPHA_3:
            return self.random_element(self.alpha_3_country_codes)
        else:
            raise ValueError("`representation` must be one of `alpha-2` or `alpha-3`.")
