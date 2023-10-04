import graphene
from graphene.types.json import JSONString
from saleor_oye.graphql.charts import ArtistType
from saleor_oye.graphql.labels import LabelType
from saleor_oye.graphql.releases import ArtikelType
from saleor_oye.models import Artikel, Artist, Label

__author__ = 'tkolter'


class SearchableType(graphene.Interface):
    highlight = graphene.Field(lambda: JSONString)
    score = graphene.Float()

    @classmethod
    def resolve_type(cls, instance, info):
        type = instance.hit.meta.doc_type
        if type == 'release':
            return ReleaseSearchResult
        if type == 'artist':
            return ArtistSearchResult
        if type == 'label':
            return LabelSearchResult

    def resolve_highlight(self, info):
        if hasattr(self.hit.meta, "highlight"):
            return self.hit.meta.highlight.to_dict()

    def resolve_score(self, info):
        return self.hit.meta.score


class ReleaseSearchResult(graphene.ObjectType):
    class Meta:
        interfaces = (SearchableType, )

    release = graphene.Field(lambda: ArtikelType)

    def resolve_release(self, info):
        return self.instance


class ArtistSearchResult(graphene.ObjectType):
    class Meta:
        interfaces = (SearchableType, )

    artist = graphene.Field(lambda: ArtistType)

    def resolve_artist(self, info):
        return self.instance


class LabelSearchResult(graphene.ObjectType):
    class Meta:
        interfaces = (SearchableType, )

    label = graphene.Field(lambda: LabelType)

    def resolve_label(self, info):
        return self.instance


class SearchResult(graphene.ObjectType):

    total = graphene.Int()

    results = graphene.List(lambda: SearchableType)
