from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{company_prefix}} {{last_name}}',
        '{{company_prefix}} {{last_name}} {{last_name}}',
        '{{company_prefix}} {{last_name}} {{company_suffix}}',
        '{{company_prefix}} {{last_name}} {{last_name}} {{company_suffix}}',
    )

    # From http://id.wikipedia.org/wiki/Jenis_badan_usaha
    # via
    # https://github.com/fzaninotto/faker/blob/master/src/Faker/Provider/id_ID/Company.php
    company_prefixes = (
        'PT', 'CV', 'UD', 'PD', 'Perum',
    )

    # From http://id.wikipedia.org/wiki/Jenis_badan_usaha
    # via
    # https://github.com/fzaninotto/faker/blob/master/src/Faker/Provider/id_ID/Company.php
    company_suffixes = (
        '(Persero) Tbk', 'Tbk',
    )

    def company_prefix(self):
        return self.random_element(self.company_prefixes)
