import graphene

from ..translations.mutations import ShopSettingsTranslate
from .mutations import (
    AuthorizationKeyAdd, AuthorizationKeyDelete, HomepageCollectionUpdate,
    ShopDomainUpdate, ShopFetchTaxRates, ShopSettingsUpdate)
from .types import Shop


class ShopQueries(graphene.ObjectType):
    shop = graphene.Field(Shop, description='Represents a shop resources.')

    def resolve_shop(self, _info):
        return Shop()


class ShopMutations(graphene.ObjectType):
    authorization_key_add = AuthorizationKeyAdd.Field()
    authorization_key_delete = AuthorizationKeyDelete.Field()

    homepage_collection_update = HomepageCollectionUpdate.Field()
    shop_domain_update = ShopDomainUpdate.Field()
    shop_settings_update = ShopSettingsUpdate.Field()
    shop_fetch_tax_rates = ShopFetchTaxRates.Field()
    shop_settings_translate = ShopSettingsTranslate.Field()
