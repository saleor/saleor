import graphene
from django.conf import settings

LanguageCodeEnum = graphene.Enum(
    'LanguageCodeEnum',
    [(lang[0].replace('-', '_').upper(), lang[0])
     for lang in settings.LANGUAGES])
