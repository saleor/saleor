# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):
    user_name_formats = (
        '{{last_name_female}}.{{first_name_female}}',
        '{{last_name_male}}.{{first_name_male}}',
        '{{last_name_male}}.{{first_name_male}}',
        '{{first_name_male}}.{{last_name_male}}',
        '{{first_name}}##',
        '{{first_name}}_##',
        '?{{last_name}}',
        '{{first_name}}{{year}}',
        '{{first_name}}_{{year}}',
    )

    email_formats = (
        '{{user_name}}@{{free_email_domain}}',
        '{{user_name}}@{{domain_name}}')

    free_email_domains = (
        'gmail.com',
        'yahoo.com',
        'hotmail.com',
        'mail.ru',
        'yandex.ru',
        'rambler.ru')

    tlds = ('ru', 'com', 'biz', 'info', 'net', 'org', 'edu')

    replacements = (
        ('А', 'a'), ('Б', 'b'), ('В', 'v'), ('Г', 'g'), ('Д', 'd'), ('Е', 'e'),
        ('Ё', 'e'), ('Ж', 'zh'), ('З', 'z'), ('И', 'i'), ('Й', ''), ('К', 'k'),
        ('Л', 'l'), ('М', 'm'), ('Н', 'n'), ('О', 'o'), ('П', 'p'), ('Р', 'r'),
        ('С', 's'), ('Т', 't'), ('У', 'u'), ('Ф', 'f'), ('Х', 'h'), ('Ц', 'ts'),
        ('Ч', 'ch'), ('Ш', 'sh'), ('Щ', 'shch'), ('Ъ', ''), ('Ы', 'i'),
        ('Ь', ''), ('Э', 'e'), ('Ю', 'yu'), ('Я', 'ya'), ('а', 'a'), ('б', 'b'),
        ('в', 'v'), ('г', 'g'), ('д', 'd'), ('е', 'e'), ('ё', 'e'), ('ж', 'zh'),
        ('з', 'z'), ('и', 'i'), ('й', ''), ('к', 'k'), ('л', 'l'), ('м', 'm'),
        ('н', 'n'), ('о', 'o'), ('п', 'p'), ('р', 'r'), ('с', 's'), ('т', 't'),
        ('у', 'u'), ('ф', 'f'), ('х', 'h'), ('ц', 'ts'), ('ч', 'ch'),
        ('ш', 'sh'), ('щ', 'shch'), ('ъ', ''), ('ы', 'i'), ('ь', ''),
        ('э', 'e'), ('ю', 'ju'), ('я', 'ja'),
    )
