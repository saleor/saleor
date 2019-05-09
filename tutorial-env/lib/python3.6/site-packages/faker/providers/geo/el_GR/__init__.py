# coding=utf-8

from __future__ import unicode_literals

from decimal import Decimal

from .. import Provider as GeoProvider


class Provider(GeoProvider):

    poly = (
        (40.34026, 19.15120),
        (42.21670, 26.13934),
        (35.55680, 29.38280),
        (34.15370, 22.58810),
    )

    def local_latlng(self):
        return float(self.local_latitude()), float(self.local_longitude())

    def local_latitude(self):
        latitudes = list(map(lambda t: int(t[0] * 10000000), self.poly))
        return Decimal(str(self.generator.random.randint(
            min(latitudes), max(latitudes)) / 10000000.0)).quantize(Decimal('.000001'))

    def local_longitude(self):
        longitudes = list(map(lambda t: int(t[1] * 10000000), self.poly))
        return Decimal(str(self.generator.random.randint(
            min(longitudes), max(longitudes)) / 10000000.0)).quantize(Decimal('.000001'))
