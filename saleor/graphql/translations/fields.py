import graphene

from .descriptions import TranslationDescriptions
from .enums import LanguageCodeEnum
from .resolvers import resolve_translation


class TranslationField(graphene.Field):
    def __init__(self, model, type_name, resolver=resolve_translation):
        super().__init__(
            model,
            language_code=graphene.Argument(
                LanguageCodeEnum,
                description=TranslationDescriptions.LANGUAGE_CODE.format(
                    type_name=type_name
                ),
                required=True,
            ),
            description=TranslationDescriptions.DESCRIPTION.format(type_name=type_name),
            resolver=resolver,
        )
