# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '+45(0)##########',
        '+45(0)#### ######',
        '+45 (0) #### ######',
        '+45(0) #########',
        '+45(0)#### #####',
        '0##########',
        '0#########',
        '0#### ######',
        '0#### #####',
        '(0####) ######',
        '(0####) #####',
    )
