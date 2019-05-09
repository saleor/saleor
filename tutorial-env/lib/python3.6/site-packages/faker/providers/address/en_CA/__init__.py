from __future__ import unicode_literals
import re
from ..en import Provider as AddressProvider


class Provider(AddressProvider):

    postal_code_letters = (
        'A', 'B', 'C', 'E', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S',
        'T', 'V', 'X', 'Y',
    )

    city_prefixes = ('North', 'East', 'West', 'South', 'New', 'Lake', 'Port')

    city_suffixes = (
        'town',
        'ton',
        'land',
        'ville',
        'berg',
        'burgh',
        'borough',
        'bury',
        'view',
        'port',
        'mouth',
        'stad',
        'furt',
        'chester',
        'mouth',
        'fort',
        'haven',
        'side',
        'shire')

    building_number_formats = ('#####', '####', '###')

    street_suffixes = (
        'Alley',
        'Avenue',
        'Branch',
        'Bridge',
        'Brook',
        'Brooks',
        'Burg',
        'Burgs',
        'Bypass',
        'Camp',
        'Canyon',
        'Cape',
        'Causeway',
        'Center',
        'Centers',
        'Circle',
        'Circles',
        'Cliff',
        'Cliffs',
        'Club',
        'Common',
        'Corner',
        'Corners',
        'Course',
        'Court',
        'Courts',
        'Cove',
        'Coves',
        'Creek',
        'Crescent',
        'Crest',
        'Crossing',
        'Crossroad',
        'Curve',
        'Dale',
        'Dam',
        'Divide',
        'Drive',
        'Drive',
        'Drives',
        'Estate',
        'Estates',
        'Expressway',
        'Extension',
        'Extensions',
        'Fall',
        'Falls',
        'Ferry',
        'Field',
        'Fields',
        'Flat',
        'Flats',
        'Ford',
        'Fords',
        'Forest',
        'Forge',
        'Forges',
        'Fork',
        'Forks',
        'Fort',
        'Freeway',
        'Garden',
        'Gardens',
        'Gateway',
        'Glen',
        'Glens',
        'Green',
        'Greens',
        'Grove',
        'Groves',
        'Harbor',
        'Harbors',
        'Haven',
        'Heights',
        'Highway',
        'Hill',
        'Hills',
        'Hollow',
        'Inlet',
        'Inlet',
        'Island',
        'Island',
        'Islands',
        'Islands',
        'Isle',
        'Isle',
        'Junction',
        'Junctions',
        'Key',
        'Keys',
        'Knoll',
        'Knolls',
        'Lake',
        'Lakes',
        'Land',
        'Landing',
        'Lane',
        'Light',
        'Lights',
        'Loaf',
        'Lock',
        'Locks',
        'Locks',
        'Lodge',
        'Lodge',
        'Loop',
        'Mall',
        'Manor',
        'Manors',
        'Meadow',
        'Meadows',
        'Mews',
        'Mill',
        'Mills',
        'Mission',
        'Mission',
        'Motorway',
        'Mount',
        'Mountain',
        'Mountain',
        'Mountains',
        'Mountains',
        'Neck',
        'Orchard',
        'Oval',
        'Overpass',
        'Park',
        'Parks',
        'Parkway',
        'Parkways',
        'Pass',
        'Passage',
        'Path',
        'Pike',
        'Pine',
        'Pines',
        'Place',
        'Plain',
        'Plains',
        'Plains',
        'Plaza',
        'Plaza',
        'Point',
        'Points',
        'Port',
        'Port',
        'Ports',
        'Ports',
        'Prairie',
        'Prairie',
        'Radial',
        'Ramp',
        'Ranch',
        'Rapid',
        'Rapids',
        'Rest',
        'Ridge',
        'Ridges',
        'River',
        'Road',
        'Road',
        'Roads',
        'Roads',
        'Route',
        'Row',
        'Rue',
        'Run',
        'Shoal',
        'Shoals',
        'Shore',
        'Shores',
        'Skyway',
        'Spring',
        'Springs',
        'Springs',
        'Spur',
        'Spurs',
        'Square',
        'Square',
        'Squares',
        'Squares',
        'Station',
        'Station',
        'Stravenue',
        'Stravenue',
        'Stream',
        'Stream',
        'Street',
        'Street',
        'Streets',
        'Summit',
        'Summit',
        'Terrace',
        'Throughway',
        'Trace',
        'Track',
        'Trafficway',
        'Trail',
        'Trail',
        'Tunnel',
        'Tunnel',
        'Turnpike',
        'Turnpike',
        'Underpass',
        'Union',
        'Unions',
        'Valley',
        'Valleys',
        'Via',
        'Viaduct',
        'View',
        'Views',
        'Village',
        'Village',
        'Villages',
        'Ville',
        'Vista',
        'Vista',
        'Walk',
        'Walks',
        'Wall',
        'Way',
        'Ways',
        'Well',
        'Wells')

    postal_code_formats = ('?%? %?%', '?%?%?%')

    provinces = (
        'Alberta', 'British Columbia', 'Manitoba', 'New Brunswick',
        'Newfoundland and Labrador', 'Northwest Territories',
        'New Brunswick', 'Nova Scotia', 'Nunavut', 'Ontario',
        'Prince Edward Island', 'Quebec', 'Saskatchewan', 'Yukon Territory')

    provinces_abbr = (
        'AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS',
        'NU', 'ON', 'PE', 'QC', 'SK', 'YT')

    city_formats = (
        '{{city_prefix}} {{first_name}}{{city_suffix}}',
        '{{city_prefix}} {{first_name}}',
        '{{first_name}}{{city_suffix}}',
        '{{last_name}}{{city_suffix}}',
    )
    street_name_formats = (
        '{{first_name}} {{street_suffix}}',
        '{{last_name}} {{street_suffix}}',
    )
    street_address_formats = (
        '{{building_number}} {{street_name}}',
        '{{building_number}} {{street_name}} {{secondary_address}}',
    )
    address_formats = (
        "{{street_address}}\n{{city}}, {{province_abbr}} {{postalcode}}",
    )
    secondary_address_formats = ('Apt. ###', 'Suite ###')

    def province(self):
        """
        """
        return self.random_element(self.provinces)

    def province_abbr(self):
        return self.random_element(self.provinces_abbr)

    def city_prefix(self):
        return self.random_element(self.city_prefixes)

    def secondary_address(self):
        return self.numerify(
            self.random_element(
                self.secondary_address_formats))

    def postal_code_letter(self):
        """
        Returns a random letter from the list of allowable
        letters in a canadian postal code
        """
        return self.random_element(self.postal_code_letters)

    def postcode(self):
        """
        Replaces all question mark ('?') occurrences with a random letter
        from postal_code_formats then passes result to
        numerify to insert numbers
        """
        temp = re.sub(r'\?',
                      lambda x: self.postal_code_letter(),
                      self.random_element(self.postal_code_formats))
        return self.numerify(temp)

    def postalcode(self):
        return self.postcode()
