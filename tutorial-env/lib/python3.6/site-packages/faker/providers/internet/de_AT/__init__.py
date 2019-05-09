# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'chello.at', 'gmail.com', 'gmx.at', 'kabsi.at',
    )
    tlds = ('at', 'co.at', 'com', 'net', 'org')

    replacements = (
        ('ä', 'ae'), ('Ä', 'Ae'),
        ('ö', 'oe'), ('Ö', 'Oe'),
        ('ü', 'ue'), ('Ü', 'Ue'),
        ('ß', 'ss'),
    )
