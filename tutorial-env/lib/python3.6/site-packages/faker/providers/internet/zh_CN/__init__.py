# coding=utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from .. import Provider as InternetProvider
from faker.utils.decorators import slugify


class Provider(InternetProvider):
    user_name_formats = (
        '{{last_romanized_name}}.{{first_romanized_name}}',
        '{{first_romanized_name}}.{{last_romanized_name}}',
        '{{first_romanized_name}}##',
        '?{{last_romanized_name}}',
    )

    tlds = OrderedDict((
        ('cn', 0.8),
        ('net', 0.1),
        ('com', 0.05),
        ('org', 0.05),
    ))

    second_level_domains = ('ac', 'com', 'edu', 'gov', 'mil', 'net', 'org',
                            'ah', 'bj', 'cq', 'fj', 'gd', 'gs', 'gz', 'gx',
                            'ha', 'hb', 'he', 'hi', 'hk', 'hl', 'hn', 'jl',
                            'js', 'jx', 'ln', 'mo', 'nm', 'nx', 'qh', 'sc',
                            'sd', 'sh', 'sn', 'sx', 'tj', 'xj', 'xz', 'yn', 'zj')

    domain_formats = (
        '##', '??',
        '{{first_romanized_name}}',
        '{{last_romanized_name}}',
        '{{first_romanized_name}}{{last_romanized_name}}',
        '{{last_romanized_name}}{{last_romanized_name}}',
        '{{first_romanized_name}}{{first_romanized_name}}',
    )

    @slugify
    def domain_word(self):
        pattern = self.random_element(self.domain_formats)
        if '#' in pattern or '?' in pattern:
            return self.bothify(pattern)
        else:
            return self.generator.parse(pattern)

    def domain_name(self, levels=1):
        if levels < 1:
            raise ValueError("levels must be greater than or equal to 1")
        if levels == 1:
            domain_word = self.domain_word()
            # Avoids he.cn as seen in issue #687
            while domain_word in self.second_level_domains:
                domain_word = self.domain_word()
            return domain_word + '.' + self.tld()
        elif levels == 2:
            my_tld = self.tld()
            if my_tld == 'cn':
                my_second_level = self.random_element(self.second_level_domains)
            else:
                my_second_level = self.domain_word()
            return self.domain_word() + '.' + my_second_level + '.' + my_tld
        else:
            return self.domain_word() + '.' + self.domain_name(levels - 1)
