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
        '?{{last_name}}',
        '{{first_name}}{{year}}',
    )

    email_formats = (
        '{{user_name}}@{{free_email_domain}}',
        '{{user_name}}@{{domain_name}}')

    free_email_domains = (
        'gmail.com', 'yahoo.com', 'hotmail.com', 'mail.bg', 'abv.bg', 'dir.bg',
    )

    tlds = ('bg', 'com', 'biz', 'info', 'net', 'org', 'edu')

    replacements = (
        ('Б', 'b'), ('Г', 'r'), ('Д', 'd'), ('Ж', 'zh'), ('З', 'z'), ('И', 'i'),
        ('Й', 'i'), ('Л', 'l'), ('П', 'p'), ('Ф', 'f'), ('Ц', 'ts'), ('Ч', 'ch'),
        ('Ш', 'sh'), ('Щ', 'sht'), ('Ъ', 'u'), ('Ь', ''), ('Ю', 'yu'), ('Я', 'ya'),
        ('б', 'b'), ('в', 'v'), ('д', 'd'), ('ж', 'zh'), ('з', 'z'), ('и', 'i'),
        ('й', 'i'), ('к', 'k'), ('л', 'l'), ('м', 'm'), ('н', 'n'), ('п', 'p'),
        ('т', 't'), ('ф', 'f'), ('ц', 'ts'), ('ч', 'ch'), ('ш', 'sh'), ('щ', 'sht'),
        ('ъ', 'u'), ('ь', ''), ('ю', 'yu'), ('я', 'ya'), ('Б', 'b'), ('Г', 'r'),
        ('Д', 'd'), ('Ж', 'zh'), ('З', 'z'), ('И', 'i'), ('Й', 'i'), ('Л', 'l'),
        ('П', 'p'), ('Ф', 'f'), ('Ц', 'ts'), ('Ч', 'ch'), ('Ш', 'sh'), ('Щ', 'sht'),
        ('Ъ', 'u'), ('Ь', ''), ('Ю', 'yu'), ('Я', 'ya'), ('б', 'b'), ('в', 'v'),
        ('д', 'd'), ('ж', 'zh'), ('з', 'z'), ('и', 'i'), ('й', 'i'), ('к', 'k'),
        ('л', 'l'), ('м', 'm'), ('н', 'n'), ('п', 'p'), ('т', 't'), ('ф', 'f'),
        ('ц', 'ts'), ('ч', 'ch'), ('ш', 'sh'), ('щ', 'sht'), ('ъ', 'u'), ('ь', ''),
        ('ю', 'yu'), ('я', 'ya'),
    )
