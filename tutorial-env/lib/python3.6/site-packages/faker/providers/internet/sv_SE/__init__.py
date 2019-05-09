# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'telia.com', 'gmail.com', 'swipnet.se', 'googlemail.com', 'live.se',
        'spray.se', 'yahoo.de',
    )
    tlds = ('com', 'com', 'com', 'se', 'se', 'se', 'net', 'org')

    replacements = (
        ('å', 'a'), ('Å', 'A'),
        ('ä', 'a'), ('Ä', 'A'),
        ('ö', 'o'), ('Ö', 'O'),
    )
