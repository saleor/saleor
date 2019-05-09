# coding=utf-8
from .. import Provider as BaseProvider


class Provider(BaseProvider):
    """
    A Faker provider for the Danish VAT IDs
    """

    vat_id_formats = (
        'DK########',
    )

    def vat_id(self):
        """
        Returns a random generated Danish Tax ID
        """

        return self.bothify(self.random_element(self.vat_id_formats))
