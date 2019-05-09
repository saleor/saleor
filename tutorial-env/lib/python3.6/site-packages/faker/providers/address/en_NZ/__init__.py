# coding=utf-8
from __future__ import unicode_literals
from ..en import Provider as AddressProvider


class Provider(AddressProvider):

    city_prefixes = (
        'North',
        'East',
        'West',
        'South',
        'New',
        'Lake',
        'Port',
        'Upper',
        'Lower',
        'High',
        'Mount',
    )

    city_suffixes = (
        'town', 'ton', 'land', 'ville', 'berg', 'burgh',
        'borough', 'bury', 'burn', 'ing', 'port', 'mouth', 'stone', 'ings'
        'mouth', 'fort', 'haven', 'leigh', 'side', 'gate', 'neath', 'side',
        ' Flats', ' Hill',
    )

    building_number_formats = ('%##', '%#', '%')

    street_suffixes = (
        # Most common:
        'Arcade', 'Arcade', 'Arcade',
        'Avenue', 'Avenue', 'Avenue', 'Avenue',
        'Avenue', 'Avenue', 'Avenue', 'Avenue',
        'Beach Road', 'Beach Road', 'Beach Road', 'Beach Road',
        'Crescent', 'Crescent', 'Crescent', 'Crescent', 'Crescent',
        'Drive', 'Drive', 'Drive', 'Drive',
        'Mews', 'Mews', 'Mews',
        'Place', 'Place', 'Place', 'Place',
        'Range Road', 'Range Road',
        'Road', 'Road', 'Road', 'Road', 'Road', 'Road', 'Road', 'Road', 'Road',
        'Street', 'Street', 'Street', 'Street', 'Street', 'Street', 'Street',
        'Street', 'Street', 'Street', 'Street', 'Street', 'Street', 'Street',
        'Street', 'Street', 'Street', 'Street', 'Street', 'Street', 'Street',
        'Terrace', 'Terrace', 'Terrace',
        'Way', 'Way', 'Way',

        # Other:
        'Access', 'Alley', 'Alleyway', 'Amble', 'Anchorage', 'Approach',
        'Broadway', 'Bypass', 'Causeway', 'Centre',
        'Circle', 'Circuit', 'Close', 'Concourse', 'Copse', 'Corner', 'Court',
        'Cove',
        'Crest', 'Cross', 'Crossing',
        'Cutting',
        'Esplanade',
        'Flats',
        'Gardens', 'Grove', 'Heights', 'Highway',
        'Lane', 'Line', 'Keys',
        'Parade', 'Park', 'Pass',
        'Plaza',
        'Point', 'Quay',
        'Reserve',
        'Ridge',
        'Rise',
        'Square',
        'Track', 'Trail',
        'View',
    )

    # Māori nouns commonly present in placenames.
    te_reo_parts = (
        'ara',
        'awa',
        'horo',
        'kawa',
        'koro',
        'kowhai',
        'manawa',
        'mata',
        'maunga',
        'moko',
        'motu',
        'ngauru',
        'pa'
        'papa',
        'po',
        'puke',
        'rangi',
        'rohe',
        'rongo',
        'roto',
        'tahi',
        'tai',
        'tangi',
        'tau',
        'tere',
        'tipu',
        'wai',
        'waka',
        'whaka',
        'whanga',
        'whare',
        'weka',
    )

    # Māori endings (usually adjectives) commonly present in placenames.
    te_reo_endings = (
        'hanga',
        'hope',
        'iti',
        'iti',
        'kiwi',
        'makau',
        'nui',
        'nui',
        'nui',
        'nuku',
        'roa',
        'rua',
        'tanga',
        'tapu',
        'toa',
        'whenua',
        'whero',
        'whitu',
    )

    postcode_formats = (
        # as per https://en.wikipedia.org/wiki/Postcodes_in_New_Zealand
        # Northland
        '0%##',
        # Auckland
        '1###',
        '20##',
        '21##',
        '22##',
        '23##',
        '24##',
        '25##',
        '26##',
        # Central North Island
        '3###',
        '4###',
        # Lower North Island
        '50##',
        '51##',
        '52##',
        '53##',
        '55##',
        '57##',
        '58##',
        # Wellington
        '60##',
        '61##',
        '62##',
        '64##',
        '69##',
        # Upper South Island
        '7###',
        # Christchurch
        '80##',
        '81##',
        '82##',
        '84##',
        '85##',
        '86##',
        '88##',
        '89##',
        # Southland
        '90##',
        '92##',
        '93##',
        '94##',
        '95##',
        '96##',
        '97##',
        '98##',
    )

    city_formats = (
        '{{first_name}}{{city_suffix}}',
        '{{last_name}}{{city_suffix}}',
        '{{last_name}}{{city_suffix}}',
        '{{last_name}}{{city_suffix}}',
        '{{last_name}}{{city_suffix}}',
        '{{last_name}}{{city_suffix}}',
        '{{city_prefix}} {{last_name}}{{city_suffix}}',
        '{{te_reo_first}}{{te_reo_ending}}',
        '{{te_reo_first}}{{te_reo_ending}}',
        '{{te_reo_first}}{{te_reo_ending}}',
        '{{te_reo_first}}{{te_reo_ending}}',
        '{{te_reo_first}}{{te_reo_part}}{{te_reo_ending}}',
        '{{te_reo_first}}{{te_reo_part}}{{te_reo_ending}}',
    )

    street_name_formats = (
        '{{first_name}} {{street_suffix}}',
        '{{last_name}} {{street_suffix}}',
        '{{last_name}} {{street_suffix}}',
        '{{last_name}} {{street_suffix}}',
        '{{last_name}}-{{last_name}} {{street_suffix}}',
        '{{te_reo_first}}{{te_reo_ending}} {{street_suffix}}',
        '{{te_reo_first}}{{te_reo_ending}} {{street_suffix}}',
        '{{te_reo_first}}{{te_reo_part}}{{te_reo_ending}} {{street_suffix}}',
    )

    street_address_formats = (
        '{{building_number}} {{street_name}}',
        '{{building_number}} {{street_name}}',
        '{{building_number}} {{street_name}}',
        '{{building_number}} {{street_name}}\nRD {{rd_number}}',
        '{{secondary_address}}\n{{building_number}} {{street_name}}',
        'PO Box {{building_number}}',
    )

    address_formats = (
        "{{street_address}}\n{{city}} {{postcode}}",
    )

    secondary_address_formats = (
        'Apt. %##',
        'Flat %#',
        'Suite %##',
        'Unit %#',
        'Level %',
    )

    def state(self):
        # New Zealand does not have states.
        return ''

    def te_reo_part(self):
        return self.random_element(self.te_reo_parts)

    def te_reo_first(self):
        return self.random_element(self.te_reo_parts).capitalize()

    def te_reo_ending(self):
        return self.random_element(self.te_reo_parts + self.te_reo_endings)

    def city_prefix(self):
        return self.random_element(self.city_prefixes)

    def city_suffix(self):
        return self.random_element(self.city_suffixes)

    def rd_number(self):
        return self.random_element([str(i) for i in range(1, 11)])

    def secondary_address(self):
        return self.numerify(
            self.random_element(
                self.secondary_address_formats))
