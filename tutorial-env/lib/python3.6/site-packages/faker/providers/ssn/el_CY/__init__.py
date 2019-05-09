# coding=utf-8
from .. import Provider as BaseProvider


class Provider(BaseProvider):
    """
    A Faker provider for the Cypriot VAT IDs
    """

    vat_id_formats = (
        'CY#########?',
    )

    def vat_id(self):
        """
        Returns a random generated Cypriot Tax ID
        """

        return self.bothify(self.random_element(self.vat_id_formats))
