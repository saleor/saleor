# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    # Source:
    # https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Jordan
    license_formats = (
        '{{initials}}-####',
        '{{initials}}-#####',
    )

    def initials(self):
        return self.random_element([
            '1',  # Ministers
            '2', '3',  # Parliament
            '5',  # General Government

            '6',  # Aqaba free zone
            '7', '8',  # Diplomatic
            '9',  # Temporary
            '10', '23',  # Passenger cars
            '38', '39',  # Crew cabs
            '41', '42',  # Light goods vehicles
            '44',  # Tractors
            '46',  # Motorcycles and scooters
            '50',  # Taxi
            '56',  # Small buses
            '58',  # Coaches
            '60',  # HGVs
            '70',  # Rental Cars
            '71',  # Trailer
            '90',  # Army
            '95',  # Ambulance
            '96',  # Gendarmerie
            '99',  # Police
        ])

    def license_plate(self):
        pattern = self.random_element(self.license_formats)
        return self.numerify(self.generator.parse(pattern))
