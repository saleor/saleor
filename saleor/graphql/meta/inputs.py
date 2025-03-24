import graphene


class MetadataInputDescription:
    DATA_SECURITY_WARNING = (
        "Warning: never store sensitive information, including financial data such as "
        "credit card details."
    )
    PRIVATE_METADATA_INPUT = (
        "Requires permissions to modify and to read the metadata of the object "
        "it's attached to.\n\n"
        f"{DATA_SECURITY_WARNING}"
    )
    PUBLIC_METADATA_INPUT = (
        f"Can be read by any API client authorized to read the object it's attached to."
        f"\n\n{DATA_SECURITY_WARNING}"
    )


class MetadataInput(graphene.InputObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=True, description="Value of a metadata item.")
