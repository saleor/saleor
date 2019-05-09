from .. import BaseProvider

localized = True


class Provider(BaseProvider):
    formats = ('###-###-###',)

    msisdn_formats = (
        '#############',
    )

    def phone_number(self):
        return self.numerify(self.random_element(self.formats))

    def msisdn(self):
        """ https://en.wikipedia.org/wiki/MSISDN """
        return self.numerify(self.random_element(self.msisdn_formats))
