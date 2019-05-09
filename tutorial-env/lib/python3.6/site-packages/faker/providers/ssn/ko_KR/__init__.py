# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as SsnProvider


class Provider(SsnProvider):
    ssn_formats = ("##0#0#-1######", "##0#1#-1######", "##0#2#-1######",
                   "##0#0#-2######", "##0#1#-2######", "##0#2#-2######")
