from braintree.resource import Resource
from braintree.configuration import Configuration
from braintree.subscription import Subscription
from braintree.merchant_account import MerchantAccount
from braintree.transaction import Transaction
from braintree.partner_merchant import PartnerMerchant
from braintree.oauth_access_revocation import OAuthAccessRevocation
from braintree.disbursement import Disbursement
from braintree.dispute import Dispute
from braintree.account_updater_daily_report import AccountUpdaterDailyReport
from braintree.error_result import ErrorResult
from braintree.validation_error_collection import ValidationErrorCollection
from braintree.connected_merchant_paypal_status_changed import ConnectedMerchantPayPalStatusChanged
from braintree.connected_merchant_status_transitioned import ConnectedMerchantStatusTransitioned
from braintree.ideal_payment import IdealPayment
from braintree.granted_payment_instrument_update import GrantedPaymentInstrumentUpdate
from braintree.local_payment_completed import LocalPaymentCompleted

class WebhookNotification(Resource):
    class Kind(object):
        AccountUpdaterDailyReport = "account_updater_daily_report"
        Check = "check"
        ConnectedMerchantStatusTransitioned = "connected_merchant_status_transitioned"
        ConnectedMerchantPayPalStatusChanged = "connected_merchant_paypal_status_changed"
        PartnerMerchantConnected = "partner_merchant_connected"
        PartnerMerchantDisconnected = "partner_merchant_disconnected"
        PartnerMerchantDeclined = "partner_merchant_declined"
        OAuthAccessRevoked = "oauth_access_revoked"
        SubscriptionCanceled = "subscription_canceled"
        SubscriptionChargedSuccessfully = "subscription_charged_successfully"
        SubscriptionChargedUnsuccessfully = "subscription_charged_unsuccessfully"
        SubscriptionExpired = "subscription_expired"
        SubscriptionTrialEnded = "subscription_trial_ended"
        SubscriptionWentActive = "subscription_went_active"
        SubscriptionWentPastDue = "subscription_went_past_due"
        SubMerchantAccountApproved = "sub_merchant_account_approved"
        SubMerchantAccountDeclined = "sub_merchant_account_declined"
        TransactionDisbursed = "transaction_disbursed"
        TransactionSettled = "transaction_settled"
        TransactionSettlementDeclined = "transaction_settlement_declined"
        DisbursementException = "disbursement_exception"
        Disbursement = "disbursement"
        DisputeOpened = "dispute_opened"
        DisputeLost = "dispute_lost"
        DisputeWon = "dispute_won"
        IdealPaymentComplete = "ideal_payment_complete"
        IdealPaymentFailed = "ideal_payment_failed"
        GrantedPaymentInstrumentUpdate = "granted_payment_instrument_update"
        LocalPaymentCompleted = "local_payment_completed"

    @staticmethod
    def parse(signature, payload):
        return Configuration.gateway().webhook_notification.parse(signature, payload)

    @staticmethod
    def verify(challenge):
        return Configuration.gateway().webhook_notification.verify(challenge)

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        if "source_merchant_id" not in attributes:
            self.source_merchant_id = None

        if "api_error_response" in attributes["subject"]:
            node_wrapper = attributes["subject"]["api_error_response"]
        else:
            node_wrapper = attributes["subject"]

        if "subscription" in node_wrapper:
            self.subscription = Subscription(gateway, node_wrapper['subscription'])
        elif "merchant_account" in node_wrapper:
            self.merchant_account = MerchantAccount(gateway, node_wrapper['merchant_account'])
        elif "transaction" in node_wrapper:
            self.transaction = Transaction(gateway, node_wrapper['transaction'])
        elif "connected_merchant_status_transitioned" in node_wrapper:
            self.connected_merchant_status_transitioned = ConnectedMerchantStatusTransitioned(gateway, node_wrapper['connected_merchant_status_transitioned'])
        elif "connected_merchant_paypal_status_changed" in node_wrapper:
            self.connected_merchant_paypal_status_changed = ConnectedMerchantPayPalStatusChanged(gateway, node_wrapper['connected_merchant_paypal_status_changed'])
        elif "partner_merchant" in node_wrapper:
            self.partner_merchant = PartnerMerchant(gateway, node_wrapper['partner_merchant'])
        elif "oauth_application_revocation" in node_wrapper:
            self.oauth_access_revocation = OAuthAccessRevocation(node_wrapper["oauth_application_revocation"])
        elif "disbursement" in node_wrapper:
            self.disbursement = Disbursement(gateway, node_wrapper['disbursement'])
        elif "dispute" in node_wrapper:
            self.dispute = Dispute(node_wrapper['dispute'])
        elif "account_updater_daily_report" in node_wrapper:
            self.account_updater_daily_report = AccountUpdaterDailyReport(gateway, node_wrapper['account_updater_daily_report'])
        elif "ideal_payment" in node_wrapper:
            self.ideal_payment = IdealPayment(gateway, node_wrapper['ideal_payment'])
        elif "granted_payment_instrument_update" in node_wrapper:
            self.granted_payment_instrument_update = GrantedPaymentInstrumentUpdate(gateway, node_wrapper["granted_payment_instrument_update"])
        elif "local_payment" in node_wrapper:
            self.local_payment_completed = LocalPaymentCompleted(gateway, node_wrapper["local_payment"])

        if "errors" in node_wrapper:
            self.errors = ValidationErrorCollection(node_wrapper['errors'])
            self.message = node_wrapper['message']
