# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'gmail.com',
        'yahoo.com',
        'hotmail.com',
        'inspire.net.nz',
        'xtra.co.nz',
    )

    tlds = (
        'nz',
        'co.nz',
        'org.nz',
        'kiwi',
        'kiwi.nz',
        'geek.nz',
        'net.nz',
        'school.nz',
        'ac.nz',
        'maori.nz',
    )
