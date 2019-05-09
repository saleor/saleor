# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} {{last_name}} {{company_suffix}}',
        '{{last_name}} & {{last_name}} {{company_suffix}}',
    )

    company_suffixes = (
        'AB', 'HB',
    )
