import graphene
from django.conf import settings

LanguageCode = graphene.Enum(
    "LanguageCode",
    [(lang[0].replace("-", "_").upper(), lang[0]) for lang in settings.LANGUAGES],
)
