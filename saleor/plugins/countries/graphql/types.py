from ....graphql.core.connection import CountableConnection, CountableDjangoObjectType
from ....graphql.translations.fields import TranslationField
from .. import models
from .translations import ProvinceTranslation


class Province(CountableDjangoObjectType):
    translation = TranslationField(
        ProvinceTranslation,
        type_name="province",
    )

    class Meta:
        model = models.Province


class ProvinceCountableConnection(CountableConnection):
    class Meta:
        node = Province
