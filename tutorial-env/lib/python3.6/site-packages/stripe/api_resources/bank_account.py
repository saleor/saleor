from __future__ import absolute_import, division, print_function

from stripe import error, util
from stripe.api_resources.account import Account
from stripe.api_resources.customer import Customer
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import DeletableAPIResource
from stripe.api_resources.abstract import VerifyMixin
from stripe.six.moves.urllib.parse import quote_plus


class BankAccount(UpdateableAPIResource, DeletableAPIResource, VerifyMixin):
    OBJECT_NAME = "bank_account"

    def instance_url(self):
        token = util.utf8(self.id)
        extn = quote_plus(token)
        if hasattr(self, "customer"):
            customer = util.utf8(self.customer)

            base = Customer.class_url()
            owner_extn = quote_plus(customer)
            class_base = "sources"

        elif hasattr(self, "account"):
            account = util.utf8(self.account)

            base = Account.class_url()
            owner_extn = quote_plus(account)
            class_base = "external_accounts"

        else:
            raise error.InvalidRequestError(
                "Could not determine whether bank_account_id %s is "
                "attached to a customer or an account." % token,
                "id",
            )

        return "%s/%s/%s/%s" % (base, owner_extn, class_base, extn)

    @classmethod
    def modify(cls, sid, **params):
        raise NotImplementedError(
            "Can't modify a bank account without a customer or account ID. "
            "Call save on customer.sources.retrieve('bank_account_id') or "
            "account.external_accounts.retrieve('bank_account_id') instead."
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
            "Can't retrieve a bank account without a customer or account ID. "
            "Use customer.sources.retrieve('bank_account_id') or "
            "account.external_accounts.retrieve('bank_account_id') instead."
        )
