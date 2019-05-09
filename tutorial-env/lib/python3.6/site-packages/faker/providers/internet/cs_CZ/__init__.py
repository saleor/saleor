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
        'seznam.cz',
        'gmail.com',
        'email.cz',
        'post.cz',
        'chello.cz',
        'centrum.cz',
        'volny.cz',
    )

    tlds = ('cz', 'com', 'cz')
