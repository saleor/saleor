import graphene


class MetadataInputDescription:
    DATA_SECURITY_WARNING = (
        "Warning: never store sensitive information, including financial data such as "
        "credit card details."
    )
    PRIVATE_METADATA_INPUT = (
        "Requires staff or app authorization to the object to modify and access.\n\n"
        f"{DATA_SECURITY_WARNING}"
    )
    PUBLIC_METADATA_INPUT = (
        f"Can be accessed without permissions.\n\n{DATA_SECURITY_WARNING}"
    )


class MetadataInput(graphene.InputObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=True, description="Value of a metadata item.")
