import graphene

from ....graphql.translations.types import BaseTranslationType
from .. import models


class ProvinceTranslation(BaseTranslationType):
    class Meta:
        model = models.Province
        interfaces = [graphene.relay.Node]
        only_fields = ["name"]
