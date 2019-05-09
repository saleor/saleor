# coding=utf-8
from __future__ import unicode_literals

from .. import Provider as AddressProvider


class Provider(AddressProvider):
    city_suffixes = ['berg', 'borg', 'by', 'bø', 'dal', 'eid', 'fjell',
                     'fjord', 'foss', 'grunn', 'hamn', 'havn', 'helle', 'mark',
                     'nes', 'odden', 'sand', 'sjøen', 'stad', 'strand',
                     'strøm', 'sund', 'vik', 'vær', 'våg', 'ø', 'øy', 'ås']
    street_suffixes = ['alléen', 'bakken', 'berget', 'bråten', 'eggen',
                       'engen', 'ekra', 'faret', 'flata', 'gata', 'gjerdet',
                       'grenda', 'gropa', 'hagen', 'haugen', 'havna', 'holtet',
                       'høgda', 'jordet', 'kollen', 'kroken', 'lia', 'lunden',
                       'lyngen', 'løkka', 'marka', 'moen', 'myra', 'plassen',
                       'ringen', 'roa', 'røa', 'skogen', 'skrenten',
                       'spranget', 'stien', 'stranda', 'stubben', 'stykket',
                       'svingen', 'tjernet', 'toppen', 'tunet', 'vollen',
                       'vika', 'åsen']
    city_formats = [
        '{{first_name}}{{city_suffix}}', '{{last_name}}']
    street_name_formats = [
        '{{last_name}}{{street_suffix}}',
    ]
    street_address_formats = ('{{street_name}} {{building_number}}',)
    address_formats = ('{{street_address}}, {{postcode}} {{city}}',)
    building_number_formats = ('%', '%', '%', '%?', '##', '##', '##?', '###')
    building_number_suffixes = {
        'A': 0.2, 'B': 0.2, 'C': 0.2, 'D': 0.1, 'E': 0.1, 'F': 0.1, 'G': 0.05,
        'H': 0.05}
    postcode_formats = ('####',)

    def building_number(self):
        suffix = self.random_element(self.building_number_suffixes)
        return self.numerify(
            self.random_element(
                self.building_number_formats)).replace(
            '?', suffix)

    def city_suffix(self):
        return self.random_element(self.city_suffixes)

    def street_suffix(self):
        return self.random_element(self.street_suffixes)
