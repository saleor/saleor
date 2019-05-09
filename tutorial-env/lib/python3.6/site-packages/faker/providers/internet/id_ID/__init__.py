# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):
    tlds = (
        # From https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains
        'com', 'org', 'net', 'int', 'edu', 'gov', 'mil',

        # From https://id.wikipedia.org/wiki/.id
        'id', 'ac.id', 'biz.id', 'co.id', 'desa.id', 'go.id', 'mil.id',
        'my.id', 'net.id', 'or.id', 'ponpes.id', 'sch.id', 'web.id',
    )
