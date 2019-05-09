# https://github.com/graphql-python/graphene/issues/425
# Adapted for Graphene 2.0

from graphene.types.enum import Enum, EnumOptions
from graphene.types.inputobjecttype import InputObjectType
from graphene.types.objecttype import ObjectType, ObjectTypeOptions


# ObjectType
class SpecialOptions(ObjectTypeOptions):
    other_attr = None


class SpecialObjectType(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, other_attr="default", **options):
        _meta = SpecialOptions(cls)
        _meta.other_attr = other_attr
        super(SpecialObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, **options
        )


def test_special_objecttype_could_be_subclassed():
    class MyType(SpecialObjectType):
        class Meta:
            other_attr = "yeah!"

    assert MyType._meta.other_attr == "yeah!"


def test_special_objecttype_could_be_subclassed_default():
    class MyType(SpecialObjectType):
        pass

    assert MyType._meta.other_attr == "default"


def test_special_objecttype_inherit_meta_options():
    class MyType(SpecialObjectType):
        pass

    assert MyType._meta.name == "MyType"
    assert MyType._meta.default_resolver is None
    assert MyType._meta.interfaces == ()


# InputObjectType
class SpecialInputObjectTypeOptions(ObjectTypeOptions):
    other_attr = None


class SpecialInputObjectType(InputObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, other_attr="default", **options):
        _meta = SpecialInputObjectTypeOptions(cls)
        _meta.other_attr = other_attr
        super(SpecialInputObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, **options
        )


def test_special_inputobjecttype_could_be_subclassed():
    class MyInputObjectType(SpecialInputObjectType):
        class Meta:
            other_attr = "yeah!"

    assert MyInputObjectType._meta.other_attr == "yeah!"


def test_special_inputobjecttype_could_be_subclassed_default():
    class MyInputObjectType(SpecialInputObjectType):
        pass

    assert MyInputObjectType._meta.other_attr == "default"


def test_special_inputobjecttype_inherit_meta_options():
    class MyInputObjectType(SpecialInputObjectType):
        pass

    assert MyInputObjectType._meta.name == "MyInputObjectType"


# Enum
class SpecialEnumOptions(EnumOptions):
    other_attr = None


class SpecialEnum(Enum):
    @classmethod
    def __init_subclass_with_meta__(cls, other_attr="default", **options):
        _meta = SpecialEnumOptions(cls)
        _meta.other_attr = other_attr
        super(SpecialEnum, cls).__init_subclass_with_meta__(_meta=_meta, **options)


def test_special_enum_could_be_subclassed():
    class MyEnum(SpecialEnum):
        class Meta:
            other_attr = "yeah!"

    assert MyEnum._meta.other_attr == "yeah!"


def test_special_enum_could_be_subclassed_default():
    class MyEnum(SpecialEnum):
        pass

    assert MyEnum._meta.other_attr == "default"


def test_special_enum_inherit_meta_options():
    class MyEnum(SpecialEnum):
        pass

    assert MyEnum._meta.name == "MyEnum"
