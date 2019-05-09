from decimal import Decimal
from braintree.attribute_getter import AttributeGetter
from braintree.transaction_details import TransactionDetails
from braintree.dispute_details import DisputeEvidence, DisputeStatusHistory
from braintree.configuration import Configuration

class Dispute(AttributeGetter):
    class Status(object):
        """
        Constants representing dispute statuses. Available types are:

        * braintree.Dispute.Status.Accepted
        * braintree.Dispute.Status.Disputed
        * braintree.Dispute.Status.Open
        * braintree.Dispute.Status.Won
        * braintree.Dispute.Status.Lost
        """
        Accepted = "accepted"
        Disputed = "disputed"
        Expired = "expired"
        Open  = "open"
        Won  = "won"
        Lost = "lost"

    class Reason(object):
        """
        Constants representing dispute reasons. Available types are:

        * braintree.Dispute.Reason.CancelledRecurringTransaction
        * braintree.Dispute.Reason.CreditNotProcessed
        * braintree.Dispute.Reason.Duplicate
        * braintree.Dispute.Reason.Fraud
        * braintree.Dispute.Reason.General
        * braintree.Dispute.Reason.InvalidAccount
        * braintree.Dispute.Reason.NotRecognized
        * braintree.Dispute.Reason.ProductNotReceived
        * braintree.Dispute.Reason.ProductUnsatisfactory
        * braintree.Dispute.Reason.Retrieval
        * braintree.Dispute.Reason.TransactionAmountDiffers
        """
        CancelledRecurringTransaction = "cancelled_recurring_transaction"
        CreditNotProcessed            = "credit_not_processed"
        Duplicate                     = "duplicate"
        Fraud                         = "fraud"
        General                       = "general"
        InvalidAccount                = "invalid_account"
        NotRecognized                 = "not_recognized"
        ProductNotReceived            = "product_not_received"
        ProductUnsatisfactory         = "product_unsatisfactory"
        Retrieval                     = "retrieval"
        TransactionAmountDiffers      = "transaction_amount_differs"

    class Kind(object):
        """
        Constants representing dispute kinds. Available types are:

        * braintree.Dispute.Kind.Chargeback
        * braintree.Dispute.Kind.PreArbitration
        * braintree.Dispute.Kind.Retrieval
        """
        Chargeback     = "chargeback"
        PreArbitration = "pre_arbitration"
        Retrieval      = "retrieval"

    @staticmethod
    def accept(id):
        """
        Accept a dispute, given a dispute_id.
        This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided dispute_id
        is not found. ::

            result = braintree.Dispute.accept("my_dispute_id")
        """

        return Configuration.gateway().dispute.accept(id)

    @staticmethod
    def add_file_evidence(dispute_id, document_upload_id):
        """
        Adds file evidence to a dispute, given a dispute_id and a document_upload_id.

        This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided dispute_id
        is not found. ::

            document = braintree.DocumentUpload.create({
                "kind": braintree.DocumentUpload.Kind.EvidenceDocument,
                "file": open("/path/to/evidence.pdf", "rb")
            })

            result = braintree.Dispute.add_file_evidence("my_dispute_id", document.id)
        """

        return Configuration.gateway().dispute.add_file_evidence(dispute_id, document_upload_id)

    @staticmethod
    def add_text_evidence(id, content_or_request):
        """
        Adds text evidence to a dispute, given a dispute_id.

        This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided dispute_id
        is not found. ::

            result = braintree.Dispute.add_text_evidence("my_dispute_id", "my_evidence")

            or

            result = braintree.Dispute.add_text_evidence("my_dispute_id", { "content": "UPS", "tag": "CARRIER_NAME", "sequence_number": "1" })
        """
        return Configuration.gateway().dispute.add_text_evidence(id, content_or_request)

    @staticmethod
    def finalize(id):
        """
        Finalize a dispute, given a dispute_id.
        This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided dispute_id
        is not found. ::

            result = braintree.Dispute.finalize("my_dispute_id")
        """

        return Configuration.gateway().dispute.finalize(id)

    @staticmethod
    def find(id):
        """
        Find an dispute, given a dispute_id.  This does not return a result
        object.  This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided dispute_id
        is not found. ::

            dispute = braintree.Dispute.find("my_dispute_id")
        """

        return Configuration.gateway().dispute.find(id)

    @staticmethod
    def remove_evidence(id, evidence_id):
        """
        Remove evidence on a dispute.
        This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided dispute_id or evidence_id
        is not found. ::

            result = braintree.Dispute.remove_evidence("my_dispute_id", "my_evidence_id")
        """

        return Configuration.gateway().dispute.remove_evidence(id, evidence_id)

    @staticmethod
    def search(*query):
        """
        Searches for disputes, given a DisputeSearch query.

            collection = braintree.Dispute.search([
                braintree.DisputeSearch.id == "the_dispute_id"
            ])

            for dispute in collection.items:
                print dispute.id
        """

        return Configuration.gateway().dispute.search(*query)

    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)

        if "amount" in attributes and self.amount is not None:
            self.amount = Decimal(self.amount)
        if "amount_disputed" in attributes and self.amount_disputed is not None:
            self.amount_disputed = Decimal(self.amount_disputed)
        if "amount_won" in attributes and self.amount_won is not None:
            self.amount_won = Decimal(self.amount_won)
        if "transaction" in attributes:
            self.transaction_details = TransactionDetails(attributes.pop("transaction"))
            self.transaction = self.transaction_details
        if "evidence" in attributes and self.evidence is not None:
            self.evidence = [DisputeEvidence(evidence) for evidence in self.evidence]
        if "status_history" in attributes and self.status_history is not None:
            self.status_history = [DisputeStatusHistory(status_history) for status_history in self.status_history]
