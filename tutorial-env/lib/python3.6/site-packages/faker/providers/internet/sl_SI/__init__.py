# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider


class Provider(InternetProvider):

    user_name_formats = (
        '{{last_name}}.{{first_name_female}}',
        '{{last_name}}.{{first_name_male}}',
        '{{first_name_female}}.{{last_name}}',
        '{{first_name_male}}.{{last_name}}',
        '{{first_name}}##',
    )

    email_formats = ('{{user_name}}@{{free_email_domain}}', )

    free_email_domains = (
        'gmail.com', 'siol.net', 'email.si', 'volja.net',
    )

    uri_pages = (
        'index', 'domov', 'iskanje', 'main', 'novica',
        'homepage', 'kategorija', 'registracija', 'login',
        'faq', 'o-nas', 'pogoji',
        'zasebnost', 'avtor',
    )
    uri_paths = (
        'app', 'main', 'wp-content', 'iskanje', 'kategorija', 'novica',
        'kategorije', 'novice', 'blog', 'komentarji', 'seznam')
    uri_extensions = (
        '.html', '.html', '.html', '.htm', '.htm', '.php',
        '.php', '.jsp', '.asp',
    )

    tlds = ('si', 'com')
