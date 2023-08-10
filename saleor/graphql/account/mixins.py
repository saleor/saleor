class AddressMetadataMixin:
    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        cls.update_metadata(instance, cleaned_data.pop("metadata", list()))  # type: ignore[attr-defined] # noqa: E501
        return super().construct_instance(instance, cleaned_data)  # type: ignore[misc] # noqa: E501
