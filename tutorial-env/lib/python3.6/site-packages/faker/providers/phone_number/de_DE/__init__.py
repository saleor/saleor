# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    # https://de.wikipedia.org/wiki/Rufnummer#Schreibweisen
    formats = (
        '+49(0)##########',
        '+49(0)#### ######',
        '+49 (0) #### ######',
        '+49(0) #########',
        '+49(0)#### #####',
        '0##########',
        '0#########',
        '0#### ######',
        '0#### #####',
        '(0####) ######',
        '(0####) #####',
    )
