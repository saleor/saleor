# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = [
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} {{company_suffix}}',
        '{{last_name}}-{{last_name}} {{company_suffix}}',
        '{{last_name}}, {{last_name}} og {{last_name}}',
        '{{last_name}}-{{last_name}}',
    ]

    company_suffixes = [
        'Gruppen', 'AS', 'ASA', 'BA', 'RFH', 'og Sønner', '& co.',
    ]
