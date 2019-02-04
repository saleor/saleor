from textwrap import dedent

import graphene

from ..enums import PermissionEnum
from .money import VAT


class CountryDisplay(graphene.ObjectType):
    code = graphene.String(description='Country code.', required=True)
    country = graphene.String(description='Country name.', required=True)
    vat = graphene.Field(VAT, description='Country tax.')


class Error(graphene.ObjectType):
    field = graphene.String(
        description=dedent("""Name of a field that caused the error. A value of
        `null` indicates that the error isn't associated with a particular
        field."""), required=False)
    message = graphene.String(description='The error message.')

    class Meta:
        description = 'Represents an error in the input of a mutation.'


class LanguageDisplay(graphene.ObjectType):
    code = graphene.String(description='Language code.', required=True)
    language = graphene.String(description='Language.', required=True)


class PermissionDisplay(graphene.ObjectType):
    code = PermissionEnum(
        description='Internal code for permission.', required=True)
    name = graphene.String(
        description='Describe action(s) allowed to do by permission.',
        required=True)

    class Meta:
        description = 'Represents a permission object in a friendly form.'


class SeoInput(graphene.InputObjectType):
    title = graphene.String(description='SEO title.')
    description = graphene.String(description='SEO description.')


class Weight(graphene.ObjectType):
    unit = graphene.String(description='Weight unit', required=True)
    value = graphene.Float(description='Weight value', required=True)

    class Meta:
        description = 'Represents weight value in a specific weight unit.'
