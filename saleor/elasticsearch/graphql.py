import graphene
from graphene.types.json import JSONString
from saleor_oye.graphql.charts import ArtistType
from saleor_oye.graphql.releases import ArtikelType
from saleor_oye.models import Artikel, Artist

__author__ = 'tkolter'


class SearchableType(graphene.Interface):
    highlight = graphene.Field(lambda: JSONString)
    score = graphene.Float()

    @classmethod
    def resolve_type(cls, instance, context, info):
        type = instance.meta.doc_type
        if type == 'release':
            return ReleaseSearchResult
        if type == 'artist':
            return ArtistSearchResult

    def resolve_highlight(self, *args):
        if hasattr(self.meta, "highlight"):
            return self.meta.highlight.to_dict()

    def resolve_score(self, *args):
        return self.meta.score


class ReleaseSearchResult(graphene.ObjectType):
    class Meta:
        interfaces = (SearchableType, )

    release = graphene.Field(lambda: ArtikelType)

    def resolve_release(self, *args):
        try:
            return Artikel.objects.get(pk=self.meta.id, webready=1)
        except Artikel.DoesNotExist:
            pass


class ArtistSearchResult(graphene.ObjectType):
    class Meta:
        interfaces = (SearchableType, )

    artist = graphene.Field(lambda: ArtistType)

    def resolve_artist(self, *args):
        try:
            return Artist.objects.get(pk=self.meta.id)
        except Artist.DoesNotExist:
            pass


class SearchResult(graphene.ObjectType):

    total = graphene.Int()

    results = graphene.List(lambda: SearchableType)
