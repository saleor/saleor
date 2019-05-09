# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider
from faker.utils.decorators import slugify


class Provider(InternetProvider):
    user_name_formats = (
        '{{last_romanized_name}}.{{first_romanized_name}}',
        '{{first_romanized_name}}.{{last_romanized_name}}',
        '{{first_romanized_name}}##',
        '?{{last_romanized_name}}',
    )
    tlds = ('com', 'com', 'com', 'net', 'org', 'tw', 'tw', 'tw')

    @slugify
    def domain_word(self):
        return self.generator.format('last_romanized_name')
