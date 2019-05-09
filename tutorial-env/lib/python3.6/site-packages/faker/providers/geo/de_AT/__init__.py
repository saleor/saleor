# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as GeoProvider


class Provider(GeoProvider):

    def local_latitude(self):
        return self.coordinate(center=47.60707, radius=1)

    def local_longitude(self):
        return self.coordinate(center=13.37208, radius=2)
