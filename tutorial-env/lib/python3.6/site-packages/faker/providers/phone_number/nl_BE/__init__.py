# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '0### ######',
        '0## #######',
        '+32### ######',
        '+32## #######',
        '+32(0)### ######',
        '+32(0)## #######',
        '(0###) ######',
        '(0##) #######',
        '0###-######',
        '0##-#######',
        '+32###-######',
        '+32##-#######',
        '+32(0)###-######',
        '+32(0)##-#######',
        '(0###)-######',
        '(0##)-#######',
    )
