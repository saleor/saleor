# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):
    safe_email_tlds = ('com', 'net', 'br', 'br')
    free_email_domains = (
        'gmail.com',
        'hotmail.com',
        'yahoo.com.br',
        'uol.com.br',
        'bol.com.br',
        'ig.com.br')
    tlds = ('com', 'com', 'com', 'net', 'org', 'br', 'br', 'br')
    replacements = (
        ('à', 'a'), ('â', 'a'), ('ã', 'a'),
        ('ç', 'c'),
        ('é', 'e'), ('ê', 'e'),
        ('í', 'i'),
        ('ô', 'o'), ('ö', 'o'), ('õ', 'o'),
        ('ú', 'u'),
    )
