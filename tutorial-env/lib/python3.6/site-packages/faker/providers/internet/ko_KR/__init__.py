# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'gmail.com', 'daum.net', 'hotmail.com', 'hanmail.net',
        'naver.com', 'nate.com', 'live.com', 'dreamwiz.com',
    )
    tlds = ('com', 'com', 'com', 'kr', 'kr', 'net', 'org')
