from __future__ import absolute_import, division, print_function

from stripe import error, util
from stripe.api_resources.account import Account
from stripe.api_resources.customer import Customer
from stripe.api_resources.recipient import Recipient
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import DeletableAPIResource
from stripe.six.moves.urllib.parse import quote_plus


class Card(UpdateableAPIResource, DeletableAPIResource):
    OBJECT_NAME = "card"

    def instance_url(self):
        token = util.utf8(self.id)
        extn = quote_plus(token)
        if hasattr(self, "customer"):
            customer = util.utf8(self.customer)

            base = Customer.class_url()
            owner_extn = quote_plus(customer)
            class_base = "sources"

        elif hasattr(self, "recipient"):
            recipient = util.utf8(self.recipient)

            base = Recipient.class_url()
            owner_extn = quote_plus(recipient)
            class_base = "cards"

        elif hasattr(self, "account"):
            account = util.utf8(self.account)

            base = Account.class_url()
            owner_extn = quote_plus(account)
            class_base = "external_accounts"

        else:
            raise error.InvalidRequestError(
                "Could not determine whether card_id %s is "
                "attached to a customer, recipient, or "
                "account." % token,
                "id",
            )

        return "%s/%s/%s/%s" % (base, owner_extn, class_base, extn)

    @classmethod
    def modify(cls, sid, **params):
        raise NotImplementedError(
            "Can't modify a card without a customer, recipient or account "
            "ID. Call save on customer.sources.retrieve('card_id'), "
            "recipient.cards.retrieve('card_id'), or "
            "account.external_accounts.retrieve('card_id') instead."
        )

    @classmethod
    def retrieve(
        cls,
        id,
        api_key=None,
        stripe_version=None,
        stripe_account=None,
        **params
    ):
        raise NotImplementedError(
            "Can't retrieve a card without a customer, recipient or account "
            "ID. Use customer.sources.retrieve('card_id'), "
            "recipient.cards.retrieve('card_id'), or "
            "account.external_accounts.retrieve('card_id') instead."
        )
