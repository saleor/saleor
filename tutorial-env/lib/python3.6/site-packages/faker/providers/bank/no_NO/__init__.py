from .. import Provider as BankProvider


class Provider(BankProvider):
    bban_format = '###########'
    country_code = 'NO'
