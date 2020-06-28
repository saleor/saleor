import django_filters

from saleor.graphql.core.filters import ObjectTypeFilter
from saleor.graphql.core.types import FilterInputObjectType
from saleor.product.models import ProductType
from ..meta.mutations import MetadataInput


def filter_product_type_metadata(qs, key, value):
    if not key or not value:
        return qs

    json_dict = {
        value.key: value.value
    }
    if key == 'private_metadata':
        qs = ProductType.objects.filter(private_metadata__contains=json_dict)
    elif key == 'metadata':
        qs = ProductType.objects.filter(metadata__contains=json_dict)

    return qs



class ProductTypeMetadataFilter(django_filters.FilterSet):

    # TODO: generic metadata filter to inherit from
    # def __init__(self):
    #     metaFileds = ["private_metadata", "metadata"]
    #     super().Meta.fields.extend(metaFileds)

    private_metadata = ObjectTypeFilter(input_class=MetadataInput,
                                        method=filter_product_type_metadata)
    metadata = ObjectTypeFilter(input_class=MetadataInput,
                                method=filter_product_type_metadata)

    class Meta:
        model = ProductType
        fields = ["private_metadata", "metadata"]


class ProductTypeMetadataFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductTypeMetadataFilter
