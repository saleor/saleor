# Copyright (c) 2007, Robert Coup <robert.coup@onetrackmind.co.nz>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#   3. Neither the name of Distance nor the names of its contributors may be used
#      to endorse or promote products derived from this software without
#      specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
Distance and Area objects to allow for sensible and convenient calculation
and conversions.

Authors: Robert Coup, Justin Bronn, Riccardo Di Virgilio

Inspired by GeoPy (http://exogen.case.edu/projects/geopy/)
and Geoff Biggs' PhD work on dimensioned units for robotics.
"""
from measurement.base import MeasureBase, NUMERIC_TYPES, pretty_name


__all__ = [
    'Distance',
    'Area',
]


AREA_PREFIX = "sq_"


class Distance(MeasureBase):
    STANDARD_UNIT = "m"
    UNITS = {
        'chain': 20.1168,
        'chain_benoit': 20.116782,
        'chain_sears': 20.1167645,
        'british_chain_benoit': 20.1167824944,
        'british_chain_sears': 20.1167651216,
        'british_chain_sears_truncated': 20.116756,
        'british_ft': 0.304799471539,
        'british_yd': 0.914398414616,
        'clarke_ft': 0.3047972654,
        'clarke_link': 0.201166195164,
        'fathom':  1.8288,
        'ft': 0.3048,
        'german_m': 1.0000135965,
        'gold_coast_ft': 0.304799710181508,
        'indian_yd': 0.914398530744,
        'inch': 0.0254,
        'link': 0.201168,
        'link_benoit': 0.20116782,
        'link_sears': 0.20116765,
        'm': 1.0,
        'mi': 1609.344,
        'nm_uk': 1853.184,
        'rod': 5.0292,
        'sears_yd': 0.91439841,
        'survey_ft': 0.304800609601,
        'yd': 0.9144,
    }
    SI_UNITS = [
        'm'
    ]

    # Unit aliases for `UNIT` terms encountered in Spatial Reference WKT.
    ALIAS = {
        'foot': 'ft',
        'inches': 'inch',
        'in': 'inch',
        'meter': 'm',
        'metre': 'm',
        'mile': 'mi',
        'yard': 'yd',
        'British chain (Benoit 1895 B)': 'british_chain_benoit',
        'British chain (Sears 1922)': 'british_chain_sears',
        'British chain (Sears 1922 truncated)': (
            'british_chain_sears_truncated'
        ),
        'British foot (Sears 1922)': 'british_ft',
        'British foot': 'british_ft',
        'British yard (Sears 1922)': 'british_yd',
        'British yard': 'british_yd',
        "Clarke's Foot": 'clarke_ft',
        "Clarke's link": 'clarke_link',
        'Chain (Benoit)': 'chain_benoit',
        'Chain (Sears)': 'chain_sears',
        'Foot (International)': 'ft',
        'German legal metre': 'german_m',
        'Gold Coast foot': 'gold_coast_ft',
        'Indian yard': 'indian_yd',
        'Link (Benoit)': 'link_benoit',
        'Link (Sears)': 'link_sears',
        'Nautical Mile': 'nm',
        'Nautical Mile (UK)': 'nm_uk',
        'US survey foot': 'survey_ft',
        'U.S. Foot': 'survey_ft',
        'Yard (Indian)': 'indian_yd',
        'Yard (Sears)': 'sears_yd'
    }

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            return Area(
                default_unit=AREA_PREFIX + self._default_unit,
                **{
                    AREA_PREFIX + self.STANDARD_UNIT: (
                        self.standard * other.standard
                    )
                }
            )
        elif isinstance(other, NUMERIC_TYPES):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard * other)}
            )
        else:
            raise TypeError(
                '%(dst)s must be multiplied with number or %(dst)s' % {
                    "dst": pretty_name(self.__class__),
                }
            )


class Area(MeasureBase):
    STANDARD_UNIT = AREA_PREFIX + Distance.STANDARD_UNIT
    # Getting the square units values and the alias dictionary.
    UNITS = dict(
        [
            ('%s%s' % (AREA_PREFIX, k), v ** 2)
            for k, v in Distance.get_units().items()
        ]
    )
    ALIAS = dict(
        [
            (k, '%s%s' % (AREA_PREFIX, v))
            for k, v in Distance.get_aliases().items()
        ]
    )

    def __truediv__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard / other)}
            )
        else:
            raise TypeError(
                '%(class)s must be divided by a number' % {
                    "class": pretty_name(self)
                }
            )

    def __div__(self, other):  # Python 2 compatibility
        return type(self).__truediv__(self, other)
