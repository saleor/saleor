# coding=utf-8
"""
This module exists solely to figure how long a registrant/publication
number may be within an ISBN. The rules change based on the prefix and
language/region. This list of rules only encapsulates the 978 prefix
for English books. 978 is the largest and, until recently, the only
prefix.

The complete list of prefixes and rules can be found at
https://www.isbn-international.org/range_file_generation
"""

from collections import namedtuple

RegistrantRule = namedtuple(
    'RegistrantRule', ['min', 'max', 'registrant_length'])

# Structure: RULES[`EAN Prefix`][`Registration Group`] = [Rule1, Rule2, ...]
RULES = {
    '978': {
        '0': [
            RegistrantRule('0000000', '1999999', 2),
            RegistrantRule('2000000', '2279999', 3),
            RegistrantRule('2280000', '2289999', 4),
            RegistrantRule('2290000', '6479999', 3),
            RegistrantRule('6480000', '6489999', 7),
            RegistrantRule('6490000', '6999999', 3),
            RegistrantRule('7000000', '8499999', 4),
            RegistrantRule('8500000', '8999999', 5),
            RegistrantRule('9000000', '9499999', 6),
            RegistrantRule('9500000', '9999999', 7),
        ],
        '1': [
            RegistrantRule('0000000', '0999999', 2),
            RegistrantRule('1000000', '3999999', 3),
            RegistrantRule('4000000', '5499999', 4),
            RegistrantRule('5500000', '7319999', 5),
            RegistrantRule('7320000', '7399999', 7),
            RegistrantRule('7400000', '8697999', 5),
            RegistrantRule('8698000', '9729999', 6),
            RegistrantRule('9730000', '9877999', 4),
            RegistrantRule('9878000', '9989999', 6),
            RegistrantRule('9990000', '9999999', 7),
        ],
    },
}
