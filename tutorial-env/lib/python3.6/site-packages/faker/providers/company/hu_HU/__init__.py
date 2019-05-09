# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} {{last_name}} {{company_suffix}}',
        '{{last_name}} és {{last_name}} {{company_suffix}}',
        '{{last_name}} és társa {{company_suffix}}',
    )

    company_suffixes = ('Kft.', 'Kht.', 'Zrt.', 'Bt.', 'Nyrt.', 'Kkt.')

    def company_suffix(self):
        return self.random_element(self.company_suffixes)
