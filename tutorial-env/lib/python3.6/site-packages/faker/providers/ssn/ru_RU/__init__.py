# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as SsnProvider


class Provider(SsnProvider):
    ssn_formats = ("############",)
