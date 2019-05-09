# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'aol.de', 'gmail.com', 'gmx.de', 'googlemail.com', 'hotmail.de',
        'web.de', 'yahoo.de',
    )
    tlds = ('com', 'com', 'com', 'net', 'org', 'de', 'de', 'de')

    replacements = (
        ('ä', 'ae'), ('Ä', 'Ae'),
        ('ö', 'oe'), ('Ö', 'Oe'),
        ('ü', 'ue'), ('Ü', 'Ue'),
        ('é', 'e'), ('É', 'E'),
        ('à', 'a'), ('À', 'A'),
        ('ß', 'ss'),
    )
