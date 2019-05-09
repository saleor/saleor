from stripe.api_resources.abstract import ListableAPIResource


class IssuerFraudRecord(ListableAPIResource):
    OBJECT_NAME = "issuer_fraud_record"
