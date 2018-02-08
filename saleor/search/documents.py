from django_elasticsearch_dsl import DocType, Index, fields
from elasticsearch_dsl import analyzer, token_filter

from ..account.models import User
from ..order.models import Order
from ..product.models import Product

storefront = Index('storefront')
storefront.settings(number_of_shards=1, number_of_replicas=0)


partial_words = token_filter(
    'partial_words', 'edge_ngram', min_gram=3, max_gram=15)
title_analyzer = analyzer(
    'title_analyzer',
    tokenizer='standard',
    filter=[partial_words, 'lowercase'])
email_analyzer = analyzer('email_analyzer', tokenizer='uax_url_email')


@storefront.doc_type
class ProductDocument(DocType):
    title = fields.StringField(analyzer=title_analyzer)

    def prepare_title(self, instance):
        return instance.name

    class Meta:
        model = Product
        fields = ['name', 'description', 'is_published']


users = Index('users')
users.settings(number_of_shards=1, number_of_replicas=0)


@users.doc_type
class UserDocument(DocType):
    user = fields.StringField(analyzer=email_analyzer)
    first_name = fields.StringField()
    last_name = fields.StringField()

    def prepare_user(self, instance):
        return instance.email

    def prepare_first_name(self, instance):
        address = instance.default_billing_address
        if address:
            return address.first_name
        return None

    def prepare_last_name(self, instance):
        address = instance.default_billing_address
        if address:
            return address.last_name
        return None

    class Meta:
        model = User
        fields = ['email']


orders = Index('orders')
orders.settings(number_of_shards=1, number_of_replicas=0)


@orders.doc_type
class OrderDocument(DocType):
    user = fields.StringField(analyzer=email_analyzer)

    def prepare_user(self, instance):
        if instance.user:
            return instance.user.email
        return instance.user_email

    class Meta:
        model = Order
        fields = ['user_email', 'discount_name']
