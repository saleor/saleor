import graphene
from graphene.types.json import JSONString
from saleor_oye.graphql.releases import ArtikelType
from saleor_oye.models import Artikel

__author__ = 'tkolter'


class SearchableType(graphene.Interface):
    highlight = graphene.Field(lambda: JSONString)

    @classmethod
    def resolve_type(cls, instance, context, info):
        type = instance.meta.doc_type
        if type == 'release':
            return ReleaseSearchResult

    def resolve_highlight(self, *args):
        if hasattr(self.meta, "highlight"):
            return self.meta.highlight.to_dict()


class ReleaseSearchResult(graphene.ObjectType):
    class Meta:
        interfaces = (SearchableType, )

    release = graphene.Field(lambda: ArtikelType)

    def resolve_release(self, *args):
        try:
            return Artikel.objects.get(pk=self.meta.id, webready=1)
        except:
            pass


class SearchResult(graphene.ObjectType):

    total = graphene.Int()

    results = graphene.List(lambda: SearchableType)
