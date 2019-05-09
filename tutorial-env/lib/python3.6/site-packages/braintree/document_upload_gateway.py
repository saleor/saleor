import braintree
import mimetypes
from braintree.document_upload import DocumentUpload
from braintree.error_result import ErrorResult
from braintree.resource import Resource
from braintree.successful_result import SuccessfulResult

class DocumentUploadGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def create(self, params={}):
        Resource.verify_keys(params, DocumentUpload.create_signature())

        if "file" in params and not hasattr(params["file"], "read"):
            raise ValueError("file must be a file handle")

        response = self.config.http().post_multipart(self.config.base_merchant_path() + "/document_uploads", *self.__payload(params))

        if "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])
        else:
            return SuccessfulResult({"document_upload": DocumentUpload(self, response["document_upload"])})

    def __file_name(self, file):
        return file.name.split("/")[-1]

    def __content_type(self, file):
        return mimetypes.guess_type(file.name)[0]

    def __payload(self, params):
        file = params.pop("file", None)
        files = {
            "file": (self.__file_name(file), file, self.__content_type(file))
        }
        params["document_upload[kind]"] = params["kind"]

        return (files, params)
