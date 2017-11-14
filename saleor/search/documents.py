from django_elasticsearch_dsl import DocType, Index
from ..product.models import Product
from ..userprofile.models import User

storefront = Index('storefront')
storefront.settings(number_of_shards=1, number_of_replicas=0)


@storefront.doc_type
class ProductDocument(DocType):
    class Meta:
        model = Product  # The model associated with this DocType

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'name',
            'description',
            'is_published'
        ]

users = Index('users')

@users.doc_type
class UserDocument(DocType):
    class Meta:
        model = User
        fields = ['email', 'is_staff']
