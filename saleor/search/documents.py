from django_elasticsearch_dsl import DocType, Index, fields
from elasticsearch_dsl import analyzer, token_filter

from ..product.models import Product

storefront = Index("storefront")
storefront.settings(number_of_shards=1, number_of_replicas=0)


partial_words = token_filter("partial_words", "edge_ngram", min_gram=3, max_gram=15)
title_analyzer = analyzer(
    "title_analyzer", tokenizer="standard", filter=[partial_words, "lowercase"]
)
email_analyzer = analyzer("email_analyzer", tokenizer="uax_url_email")


@storefront.doc_type
class ProductDocument(DocType):
    title = fields.StringField(analyzer=title_analyzer)

    def prepare_title(self, instance):
        return instance.name

    class Meta:
        model = Product
        fields = ["name", "description", "is_published"]


users = Index("users")
users.settings(number_of_shards=1, number_of_replicas=0)
