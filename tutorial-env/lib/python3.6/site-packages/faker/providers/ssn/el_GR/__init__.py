# coding=utf-8
from .. import Provider as BaseProvider


class Provider(BaseProvider):
    """
    A Faker provider for the Greek VAT IDs
    """

    vat_id_formats = (
        'EL#########',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: a random Greek VAT ID
        """

        return self.bothify(self.random_element(self.vat_id_formats))
