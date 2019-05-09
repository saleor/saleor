# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):
    safe_email_tlds = ('com', 'net', 'pt', 'pt')
    free_email_domains = ('gmail.com', 'hotmail.com', 'clix.pt', 'sapo.pt')
    tlds = ('com', 'com', 'com', 'net', 'org', 'pt', 'pt', 'pt')
