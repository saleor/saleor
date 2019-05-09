# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'gmail.com', 'googlemail.com', 'hotmail.com', 'suomi24.fi',
        'kolumbus.fi', 'luukku.com', 'surffi.net',
    )

    tlds = ('com', 'com', 'com', 'fi', 'fi', 'net', 'org')
