# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as SsnProvider


class Provider(SsnProvider):
    ssn_formats = ("?#########",)

    def ssn(self):
        return self.bothify(self.random_element(self.ssn_formats)).upper()
