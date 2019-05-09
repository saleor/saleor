# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    free_email_domains = (
        'gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com',
        'bih.net.ba', 'tel.net.ba',
    )

    tlds = ('ba', 'com.ba', 'org.ba', 'net.ba', 'gov.ba', 'edu.ba', 'unsa.ba')

    replacements = (
        ('č', 'c'), ('Č', 'C'),
        ('ć', 'c'), ('Ć', 'C'),
        ('đ', 'dj'), ('Đ', 'Dj'),
        ('š', 's'), ('Š', 'S'),
        ('ž', 'z'), ('Ž', 'Z'),
    )
