from measurement.base import MeasureBase


__all__ = [
    'Volume',
]


class Volume(MeasureBase):
    STANDARD_UNIT = 'cubic_meter'
    UNITS = {
        'us_g': 0.00378541,
        'us_qt': 0.000946353,
        'us_pint': 0.000473176,
        'us_cup': 0.000236588,
        'us_oz': 2.9574e-5,
        'us_tbsp': 1.4787e-5,
        'us_tsp': 4.9289e-6,
        'cubic_millimeter': 0.000000001,
        'cubic_centimeter': 0.000001,
        'cubic_decimeter':  0.001,
        'cubic_meter': 1.0,
        'l': 0.001,
        'cubic_foot': 0.0283168,
        'cubic_inch': 1.6387e-5,
        'imperial_g': 0.00454609,
        'imperial_qt': 0.00113652,
        'imperial_pint': 0.000568261,
        'imperial_oz': 2.8413e-5,
        'imperial_tbsp': 1.7758e-5,
        'imperial_tsp': 5.9194e-6,
    }
    ALIAS = {
        'US Gallon': 'us_g',
        'US Quart': 'us_qt',
        'US Pint': 'us_pint',
        'US Cup': 'us_cup',
        'US Ounce': 'us_oz',
        'US Fluid Ounce': 'us_oz',
        'US Tablespoon': 'us_tbsp',
        'US Teaspoon': 'us_tsp',
        'cubic millimeter': 'cubic_millimeter',
        'cubic centimeter': 'cubic_centimeter',
        'cubic decimeter': 'cubic_decimeter',
        'cubic meter': 'cubic_meter',
        'liter': 'l',
        'litre': 'l',
        'cubic foot': 'cubic_foot',
        'cubic inch': 'cubic_inch',
        'Imperial Gram': 'imperial_g',
        'Imperial Quart': 'imperial_qt',
        'Imperial Pint': 'imperial_pint',
        'Imperial Ounce': 'imperial_oz',
        'Imperial Tablespoon': 'imperial_tbsp',
        'Imperial Teaspoon': 'imperial_tsp',
    }
    SI_UNITS = ['l']

    def __init__(self, *args, **kwargs):
        super(Volume, self).__init__(*args, **kwargs)
