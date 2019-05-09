from braintree.validation_error_collection import ValidationErrorCollection

class Errors(object):
    def __init__(self, data):
        data["errors"] = []
        self.errors = ValidationErrorCollection(data)
        self.size = self.errors.deep_size

    @property
    def deep_errors(self):
        return self.errors.deep_errors

    def for_object(self, key):
        return self.errors.for_object(key)

    def __len__(self):
        return self.size
