from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.api_resources.transfer import Transfer
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.six.moves.urllib.parse import quote_plus


class Reversal(UpdateableAPIResource):
    OBJECT_NAME = "transfer_reversal"

    def instance_url(self):
        token = util.utf8(self.id)
        transfer = util.utf8(self.transfer)
        base = Transfer.class_url()
        cust_extn = quote_plus(transfer)
        extn = quote_plus(token)
        return "%s/%s/reversals/%s" % (base, cust_extn, extn)

    @classmethod
    def modify(cls, sid, **params):
        raise NotImplementedError(
            "Can't modify a reversal without a transfer"
            "ID. Call save on transfer.reversals.retrieve('reversal_id')"
        )

    @classmethod
    def retrieve(cls, id, api_key=None, **params):
        raise NotImplementedError(
            "Can't retrieve a reversal without a transfer"
            "ID. Use transfer.reversals.retrieve('reversal_id')"
        )
