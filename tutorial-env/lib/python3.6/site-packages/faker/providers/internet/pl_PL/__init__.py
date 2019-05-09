# coding=utf-8
from __future__ import unicode_literals

from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'onet.pl',
        'interia.pl',
        'gmail.com',
        'o2.pl',
        'yahoo.com',
        'hotmail.com',
    )

    tlds = ('com', 'com', 'com', 'net', 'org', 'pl', 'pl', 'pl')

    replacements = (
        ('ą', 'a'),
        ('ć', 'c'),
        ('ę', 'e'),
        ('ł', 'l'),
        ('ń', 'n'),
        ('ó', 'o'),
        ('ś', 's'),
        ('ź', 'z'),
        ('ż', 'z'),
    )
