from __future__ import unicode_literals

from ..en import Provider as AddressProvider


class Provider(AddressProvider):

    city_prefixes = ('North', 'East', 'West', 'South', 'New', 'Lake', 'Port',
                     'St.')

    city_suffixes = ('town', 'ton', 'land', 'ville', 'berg', 'burgh',
                     'borough', 'bury', 'view', 'port', 'mouth', 'stad',
                     'furt', 'chester', 'mouth', 'fort', 'haven', 'side',
                     'shire')

    building_number_formats = ('###', '##', '#')

    street_suffixes = (
        'Access', 'Alley', 'Alleyway', 'Amble', 'Anchorage', 'Approach',
        'Arcade', 'Artery', 'Avenue', 'Basin', 'Beach', 'Bend', 'Block',
        'Boulevard', 'Brace', 'Brae', 'Break', 'Bridge', 'Broadway', 'Brow',
        'Bypass', 'Byway', 'Causeway', 'Centre', 'Centreway', 'Chase',
        'Circle', 'Circlet', 'Circuit', 'Circus', 'Close', 'Colonnade',
        'Common', 'Concourse', 'Copse', 'Corner', 'Corso', 'Court',
        'Courtyard', 'Cove', 'Crescent', 'Crest', 'Cross', 'Crossing',
        'Crossroad', 'Crossway', 'Cruiseway', 'Cul-de-sac', 'Cutting', 'Dale',
        'Dell', 'Deviation', 'Dip', 'Distributor', 'Drive', 'Driveway', 'Edge',
        'Elbow', 'End', 'Entrance', 'Esplanade', 'Estate', 'Expressway',
        'Extension', 'Fairway', 'Fire Track', 'Firetrail', 'Flat', 'Follow',
        'Footway', 'Foreshore', 'Formation', 'Freeway', 'Front', 'Frontage',
        'Gap', 'Garden', 'Gardens', 'Gate', 'Gates', 'Glade', 'Glen', 'Grange',
        'Green', 'Ground', 'Grove', 'Gully', 'Heights', 'Highroad', 'Highway',
        'Hill', 'Interchange', 'Intersection', 'Junction', 'Key', 'Landing',
        'Lane', 'Laneway', 'Lees', 'Line', 'Link', 'Little', 'Lookout', 'Loop',
        'Lower', 'Mall', 'Meander', 'Mew', 'Mews', 'Motorway', 'Mount', 'Nook',
        'Outlook', 'Parade', 'Park', 'Parklands', 'Parkway', 'Part', 'Pass',
        'Path', 'Pathway', 'Piazza', 'Place', 'Plateau', 'Plaza', 'Pocket',
        'Point', 'Port', 'Promenade', 'Quad', 'Quadrangle', 'Quadrant', 'Quay',
        'Quays', 'Ramble', 'Ramp', 'Range', 'Reach', 'Reserve', 'Rest',
        'Retreat', 'Ride', 'Ridge', 'Ridgeway', 'Right Of Way', 'Ring', 'Rise',
        'River', 'Riverway', 'Riviera', 'Road', 'Roads', 'Roadside', 'Roadway',
        'Ronde', 'Rosebowl', 'Rotary', 'Round', 'Route', 'Row', 'Rue', 'Run',
        'Service Way', 'Siding', 'Slope', 'Sound', 'Spur', 'Square', 'Stairs',
        'State Highway', 'Steps', 'Strand', 'Street', 'Strip', 'Subway',
        'Tarn', 'Terrace', 'Thoroughfare', 'Tollway', 'Top', 'Tor', 'Towers',
        'Track', 'Trail', 'Trailer', 'Triangle', 'Trunkway', 'Turn',
        'Underpass', 'Upper', 'Vale', 'Viaduct', 'View', 'Villas', 'Vista',
        'Wade', 'Walk', 'Walkway', 'Way', 'Wynd')

    postcode_formats = (
        # as per https://en.wikipedia.org/wiki/Postcodes_in_Australia
        # NSW
        '1###',
        '20##',
        '21##',
        '22##',
        '23##',
        '24##',
        '25##',
        '2619',
        '262#',
        '263#',
        '264#',
        '265#',
        '266#',
        '267#',
        '268#',
        '269#',
        '27##',
        '28##',
        '292#',
        '293#',
        '294#',
        '295#',
        '296#',
        '297#',
        '298#',
        '299#',
        # ACT
        '02##',
        '260#',
        '261#',
        '290#',
        '291#',
        '2920',
        # VIC
        '3###',
        '8###',
        # QLD
        '4###',
        '9###',
        # SA
        '5###',
        # WA
        '6###',
        # TAS
        '7###',
        # NT
        '08##',
        '09##',
    )

    states = ('Australian Capital Territory', 'New South Wales',
              'Northern Territory', 'Queensland', 'South Australia',
              'Tasmania', 'Victoria', 'Western Australia')

    states_abbr = ('ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA')

    city_formats = ('{{city_prefix}} {{first_name}}{{city_suffix}}',
                    '{{city_prefix}} {{first_name}}',
                    '{{first_name}}{{city_suffix}}',
                    '{{last_name}}{{city_suffix}}')

    street_name_formats = ('{{first_name}} {{street_suffix}}',
                           '{{last_name}} {{street_suffix}}')

    street_address_formats = (
        '{{building_number}} {{street_name}}',
        '{{secondary_address}}\n {{building_number}} {{street_name}}',
    )

    address_formats = (
        "{{street_address}}\n{{city}}, {{state_abbr}}, {{postcode}}", )

    secondary_address_formats = ('Apt. ###', 'Flat ##', 'Suite ###', 'Unit ##',
                                 'Level #', '### /', '## /', '# /')

    def city_prefix(self):
        return self.random_element(self.city_prefixes)

    def secondary_address(self):
        return self.numerify(
            self.random_element(
                self.secondary_address_formats))

    def state(self):
        return self.random_element(self.states)

    def state_abbr(self):
        return self.random_element(self.states_abbr)
