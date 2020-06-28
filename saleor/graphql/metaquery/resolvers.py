from saleor.product.models import ProductType


def resolve_product_type_by_metadata(privateMetadataKey=None, metadataKey=None,
                                     privateMetadataValue=None, metadataValue=None):
    json_dict = {}
    if privateMetadataKey and privateMetadataValue:
        json_dict[privateMetadataKey] = privateMetadataValue
        qs = ProductType.objects.filter(private_metadata__contains=json_dict)
    elif metadataKey and metadataValue:
        json_dict[metadataKey] = metadataValue
        qs = ProductType.objects.filter(metadata__contains=json_dict)
    else:
        qs = ProductType.objects.none()

    return qs.first()
