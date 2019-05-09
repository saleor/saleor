# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):
    safe_email_tlds = ('com', 'net', 'eu', 'it', 'it', 'it')
    free_email_domains = (
        'libero.it', 'libero.it', 'libero.it',
        'tim.it',
        'tin.it',
        'alice.it',
        'virgilio.it',
        'tiscali.it',
        'fastwebnet.it',
        'vodafone.it',
        'poste.it',
        'gmail.com', 'gmail.com', 'gmail.com',
        'outlook.com',
        'live.com',
        'hotmail.com',
        'hotmail.it',
        'yahoo.com',
        'tele2.it',
    )
    tlds = ('com', 'com', 'com', 'net', 'org', 'eu', 'it', 'it', 'it', 'it')
    replacements = (
        ('à', 'a'), ('é', 'e'), ('è', 'e'),
        ('ì', 'i'), ('ò', 'o'), ('ù', 'u'),
    )
