import mimetypes
from braintree.successful_result import SuccessfulResult
from braintree.resource import Resource
from braintree.configuration import Configuration

class DocumentUpload(Resource):
    """
    A class representing a DocumentUpload.

    An example of creating a document upload with all available fields:

        result = braintree.DocumentUpload.create(
            {
                "kind": braintree.DocumentUpload.Kind.EvidenceDocument,
                "file": open("path/to/file", "rb"),
            }
        )

    For more information on DocumentUploads, see https://developers.braintreepayments.com/reference/request/document_upload/create

    """

    class Kind(object):
        EvidenceDocument = "evidence_document"

    @staticmethod
    def create(params={}):
        """
        Create a DocumentUpload

        File and Kind are required:

            result = braintree.DocumentUpload.create(
                {
                    "kind": braintree.DocumentUpload.Kind.EvidenceDocument,
                    "file": open("path/to/file", "rb"),
                }
            )

        """
        return Configuration.gateway().document_upload.create(params)

    @staticmethod
    def create_signature():
        return [
            "kind",
            "file",
        ]

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
