from .. import Provider as BankProvider


class Provider(BankProvider):
    bban_format = '#' * 26
    country_code = 'PL'
