# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{company_prefix}} «{{last_name}}»',
        '{{company_prefix}} «{{last_name}} {{last_name}}»',
        '{{company_prefix}} «{{last_name}}-{{last_name}}»',
        '{{company_prefix}} «{{last_name}}, {{last_name}} и {{last_name}}»',
        '{{last_name}}',
    )

    company_prefixes = (
        'РАО', 'АО', 'ИП', 'НПО',
    )

    def company_prefix(self):
        return self.random_element(self.company_prefixes)
