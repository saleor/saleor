from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.api_resources.customer import Customer
from stripe.api_resources.abstract import APIResource
from stripe.six.moves.urllib.parse import quote_plus


class TaxId(APIResource):
    OBJECT_NAME = "tax_id"

    def instance_url(self):
        token = util.utf8(self.id)
        customer = util.utf8(self.customer)
        base = Customer.class_url()
        cust_extn = quote_plus(customer)
        extn = quote_plus(token)
        return "%s/%s/tax_ids/%s" % (base, cust_extn, extn)

    @classmethod
    def retrieve(cls, id, api_key=None, **params):
        raise NotImplementedError(
            "Can't retrieve a tax id without a customer ID. Use customer.retrieve_tax_id('tax_id')"
        )
