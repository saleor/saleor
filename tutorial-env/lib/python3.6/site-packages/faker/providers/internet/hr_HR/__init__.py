# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'gmail.com', 'hotmail.com', 'yahoo.com',
        'net.hr', 'zg.t-com.hr', 'inet.hr', 't.ht.hr', 'vip.hr',
        'globalnet.hr', 'xnet.hr', 'yahoo.hr', 'zagreb.hr',
    )

    tlds = ('hr', 'com', 'com.hr', 'info', 'org', 'net', 'biz')

    replacements = (
        ('č', 'c'), ('Č', 'C'),
        ('ć', 'c'), ('Ć', 'C'),
        ('đ', 'dj'), ('Đ', 'Dj'),
        ('š', 's'), ('Š', 'S'),
        ('ž', 'z'), ('Ž', 'Z'),
    )
