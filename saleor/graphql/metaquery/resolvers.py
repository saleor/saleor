from saleor.account.models import User
from saleor.product.models import ProductType, Product


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


def resolve_user_by_metadata(privateMetadataKey=None, metadataKey=None,
                                     privateMetadataValue=None, metadataValue=None):
    json_dict = {}
    if privateMetadataKey and privateMetadataValue:
        json_dict[privateMetadataKey] = privateMetadataValue
        qs = User.objects.filter(private_metadata__contains=json_dict)
    elif metadataKey and metadataValue:
        json_dict[metadataKey] = metadataValue
        qs = User.objects.filter(metadata__contains=json_dict)
    else:
        qs = User.objects.none()

    return qs.first()

def resolve_product_by_metadata(privateMetadataKey=None, metadataKey=None,
                                     privateMetadataValue=None, metadataValue=None):
    json_dict = {}
    if privateMetadataKey and privateMetadataValue:
        json_dict[privateMetadataKey] = privateMetadataValue
        qs = Product.objects.filter(private_metadata__contains=json_dict)
    elif metadataKey and metadataValue:
        json_dict[metadataKey] = metadataValue
        qs = Product.objects.filter(metadata__contains=json_dict)
    else:
        qs = Product.objects.none()

    return qs.first()

