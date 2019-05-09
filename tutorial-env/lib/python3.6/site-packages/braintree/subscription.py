from decimal import Decimal
from braintree.util.http import Http
import braintree
import warnings
from braintree.add_on import AddOn
from braintree.descriptor import Descriptor
from braintree.discount import Discount
from braintree.exceptions.not_found_error import NotFoundError
from braintree.resource_collection import ResourceCollection
from braintree.subscription_status_event import SubscriptionStatusEvent
from braintree.successful_result import SuccessfulResult
from braintree.error_result import ErrorResult
from braintree.transaction import Transaction
from braintree.resource import Resource
from braintree.configuration import Configuration

class Subscription(Resource):
    """
    A class representing a Subscription.

    An example of creating a subscription with all available fields::

        result = braintree.Subscription.create({
            "id": "my_subscription_id",
            "merchant_account_id": "merchant_account_one",
            "payment_method_token": "my_payment_token",
            "plan_id": "some_plan_id",
            "price": "29.95",
            "trial_duration": 1,
            "trial_duration_unit": braintree.Subscription.TrialDurationUnit.Month,
            "trial_period": True
        })

    For more information on Subscriptions, see https://developers.braintreepayments.com/reference/request/subscription/create/python

    """

    class TrialDurationUnit(object):
        """
        Constants representing trial duration units.  Available types are:

        * braintree.Subscription.TrialDurationUnit.Day
        * braintree.Subscription.TrialDurationUnit.Month
        """

        Day = "day"
        Month = "month"

    class Source(object):
        Api          = "api"
        ControlPanel = "control_panel"
        Recurring    = "recurring"
        Unrecognized = "unrecognized"

    class Status(object):
        """
        Constants representing subscription statusues.  Available statuses are:

        * braintree.Subscription.Status.Active
        * braintree.Subscription.Status.Canceled
        * braintree.Subscription.Status.Expired
        * braintree.Subscription.Status.PastDue
        * braintree.Subscription.Status.Pending
        """

        Active = "Active"
        Canceled = "Canceled"
        Expired = "Expired"
        PastDue = "Past Due"
        Pending = "Pending"

    @staticmethod
    def create(params={}):
        """
        Create a Subscription

        Token and Plan are required:::

            result = braintree.Subscription.create({
                "payment_method_token": "my_payment_token",
                "plan_id": "some_plan_id",
            })

        """

        return Configuration.gateway().subscription.create(params)

    @staticmethod
    def create_signature():
        return [
            "billing_day_of_month",
            "first_billing_date",
            "id",
            "merchant_account_id",
            "never_expires",
            "number_of_billing_cycles",
            "payment_method_nonce",
            "payment_method_token",
            "plan_id",
            "price",
            "trial_duration",
            "trial_duration_unit",
            "trial_period",
            {
                "descriptor": [ "name", "phone", "url" ]
            },
            {
                "options": [
                    "do_not_inherit_add_ons_or_discounts",
                    "start_immediately",
                    { 
                        "paypal": [ "description" ] 
                    }
                ]
            }
        ] + Subscription._add_ons_discounts_signature()

    @staticmethod
    def find(subscription_id):
        """
        Find a subscription given a subscription_id.  This does not return a result
        object.  This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>`
        if the provided subscription_id is not found. ::

            subscription = braintree.Subscription.find("my_subscription_id")
        """

        return Configuration.gateway().subscription.find(subscription_id)

    @staticmethod
    def retryCharge(subscription_id, amount=None):
        warnings.warn("Please use Subscription.retry_charge instead", DeprecationWarning)
        return Subscription.retry_charge(subscription_id, amount)

    @staticmethod
    def retry_charge(subscription_id, amount=None, submit_for_settlement=False):
        return Configuration.gateway().subscription.retry_charge(subscription_id, amount, submit_for_settlement)

    @staticmethod
    def update(subscription_id, params={}):
        """
        Update an existing subscription

        By subscription_id. The params are similar to create::


            result = braintree.Subscription.update("my_subscription_id", {
                "price": "9.99",
            })

        """

        return Configuration.gateway().subscription.update(subscription_id, params)

    @staticmethod
    def cancel(subscription_id):
        """
        Cancel a subscription

        By subscription_id::

            result = braintree.Subscription.cancel("my_subscription_id")

        """

        return Configuration.gateway().subscription.cancel(subscription_id)

    @staticmethod
    def search(*query):
        """
        Allows searching on subscriptions. There are two types of fields that are searchable: text and
        multiple value fields. Searchable text fields are:
        - plan_id
        - days_past_due

        Searchable multiple value fields are:
        - status

        For text fields, you can search using the following operators: ==, !=, starts_with, ends_with
        and contains. For mutiple value fields, you can search using the in_list operator. An example::

            braintree.Subscription.search([
                braintree.SubscriptionSearch.plan_id.starts_with("abc"),
                braintree.SubscriptionSearch.days_past_due == "30",
                braintree.SubscriptionSearch.status.in_list([braintree.Subscription.Status.PastDue])
            ])
        """

        return Configuration.gateway().subscription.search(*query)

    @staticmethod
    def update_signature():
        return [
            "id",
            "merchant_account_id",
            "never_expires",
            "number_of_billing_cycles",
            "payment_method_nonce",
            "payment_method_token",
            "plan_id",
            "price",
            {
                "descriptor": [ "name", "phone", "url" ]
            },
            {
                "options": [ 
                    "prorate_charges", 
                    "replace_all_add_ons_and_discounts", 
                    "revert_subscription_on_proration_failure",
                    {
                        "paypal": [ "description" ]
                    }
                ]
            }
        ] + Subscription._add_ons_discounts_signature()

    @staticmethod
    def _add_ons_discounts_signature():
        return [
            {
                "add_ons": [{
                    "add": ["amount", "inherited_from_id", "never_expires", "number_of_billing_cycles", "quantity"],
                    "remove": ["__any_key__"],
                    "update": ["amount", "existing_id", "never_expires", "number_of_billing_cycles", "quantity"]
                }],
                "discounts": [{
                    "add": ["amount", "inherited_from_id", "never_expires", "number_of_billing_cycles", "quantity"],
                    "remove": ["__any_key__"],
                    "update": ["amount", "existing_id", "never_expires", "number_of_billing_cycles", "quantity"]
                }]
            }
        ]

    def __init__(self, gateway, attributes):
        if "next_bill_amount" in attributes:
            self._next_bill_amount = Decimal(attributes["next_bill_amount"])
            del(attributes["next_bill_amount"])
        Resource.__init__(self, gateway, attributes)
        if "price" in attributes:
            self.price = Decimal(self.price)
        if "balance" in attributes:
            self.balance = Decimal(self.balance)
        if "next_billing_period_amount" in attributes:
            self.next_billing_period_amount = Decimal(self.next_billing_period_amount)
        if "add_ons" in attributes:
            self.add_ons = [AddOn(gateway, add_on) for add_on in self.add_ons]
        if "descriptor" in attributes:
            self.descriptor = Descriptor(gateway, attributes.pop("descriptor"))
        if "description" in attributes:
            self.description = attributes["description"] 
        if "discounts" in attributes:
            self.discounts = [Discount(gateway, discount) for discount in self.discounts]
        if "status_history" in attributes:
            self.status_history = [SubscriptionStatusEvent(gateway, status_event) for status_event in self.status_history]
        if "transactions" in attributes:
            self.transactions = [Transaction(gateway, transaction) for transaction in self.transactions]

    @property
    def next_bill_amount(self):
        warnings.warn("Please use Subscription.next_billing_period_amount instead", DeprecationWarning)
        return self._next_bill_amount
