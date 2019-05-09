from ..utils.deprecated import warn_deprecation
from ..utils.subclass_with_meta import SubclassWithMeta


class AbstractType(SubclassWithMeta):
    def __init_subclass__(cls, *args, **kwargs):
        warn_deprecation(
            "Abstract type is deprecated, please use normal object inheritance instead.\n"
            "See more: https://github.com/graphql-python/graphene/blob/master/UPGRADE-v2.0.md#deprecations"
        )
        super(AbstractType, cls).__init_subclass__(*args, **kwargs)
