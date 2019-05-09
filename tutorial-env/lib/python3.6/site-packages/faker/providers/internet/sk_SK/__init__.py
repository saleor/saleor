# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):
    user_name_formats = (
        '{{last_name_female}}.{{first_name_female}}',
        '{{last_name_female}}.{{first_name_female}}',
        '{{last_name_male}}.{{first_name_male}}',
        '{{last_name_male}}.{{first_name_male}}',
        '{{first_name_female}}.{{last_name_female}}',
        '{{first_name_male}}.{{last_name_male}}',
        '{{first_name}}##',
        '?{{last_name}}',
        '?{{last_name}}',
        '?{{last_name}}',
    )

    email_formats = ('{{user_name}}@{{free_email_domain}}', )

    free_email_domains = (
        'zoznam.sk',
        'gmail.com',
        'centrum.sk',
        'post.sk',
        'chello.sk',
        'pobox.sk',
        'szm.sk',
        'atlas.sk',
        'azet.sk',
        'inmail.sk',
    )

    tlds = ('sk', 'com')
