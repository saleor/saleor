# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} {{last_name}} {{company_suffix}}',
        '{{last_name}}',
    )

    company_suffixes = (
        'АД', 'AD',
        'ADSITz', 'АДСИЦ',
        'EAD', 'ЕАД',
        'EOOD', 'ЕООД',
        'ET', 'ET',
        'OOD', 'ООД',
        'KD', 'КД',
        'KDA', 'КДА',
        'SD', 'СД',
    )
