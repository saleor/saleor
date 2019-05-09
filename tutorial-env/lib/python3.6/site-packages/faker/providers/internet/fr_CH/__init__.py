# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):
    safe_email_tlds = ('org', 'com', 'net', 'ch')
    free_email_domains = (
        'gmail.com',
        'hotmail.fr',
        'yahoo.fr',
        'bluewin.ch',
        'romandie.com',
        'hispeed.ch',
        'sunrise.ch',
        'vtxnet.ch')
    tlds = ('com', 'com', 'com', 'net', 'org', 'ch', 'ch', 'ch')

    replacements = (
        ('ä', 'ae'), ('à', 'a'), ('â', 'a'),
        ('ç', 'c'),
        ('é', 'e'), ('è', 'e'), ('ê', 'e'), ('ë', 'e'),
        ('ï', 'i'), ('î', 'i'),
        ('ö', 'oe'), ('ô', 'o'),
        ('ü', 'ue'), ('ù', 'u'), ('ü', 'u'),
        ('ß', 'ss'),
    )
