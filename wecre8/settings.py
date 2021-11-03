from saleor.settings import *

ROOT_URLCONF = "wecre8.urls"

GRAPHENE.update({
    'SCHEMA': 'wecre8.graphql.api.schema'
})
