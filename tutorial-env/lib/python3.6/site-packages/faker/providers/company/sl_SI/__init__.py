from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{first_name}} {{last_name}} s.p.',
    )

    company_suffixes = (
        'd.o.o.', 'd.d.',
    )
