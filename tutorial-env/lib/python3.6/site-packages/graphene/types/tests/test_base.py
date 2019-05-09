from ..base import BaseOptions, BaseType


class CustomOptions(BaseOptions):
    pass


class CustomType(BaseType):
    @classmethod
    def __init_subclass_with_meta__(cls, **options):
        _meta = CustomOptions(cls)
        super(CustomType, cls).__init_subclass_with_meta__(_meta=_meta, **options)


def test_basetype():
    class MyBaseType(CustomType):
        pass

    assert isinstance(MyBaseType._meta, CustomOptions)
    assert MyBaseType._meta.name == "MyBaseType"
    assert MyBaseType._meta.description is None


def test_basetype_nones():
    class MyBaseType(CustomType):
        """Documentation"""

        class Meta:
            name = None
            description = None

    assert isinstance(MyBaseType._meta, CustomOptions)
    assert MyBaseType._meta.name == "MyBaseType"
    assert MyBaseType._meta.description == "Documentation"


def test_basetype_custom():
    class MyBaseType(CustomType):
        """Documentation"""

        class Meta:
            name = "Base"
            description = "Desc"

    assert isinstance(MyBaseType._meta, CustomOptions)
    assert MyBaseType._meta.name == "Base"
    assert MyBaseType._meta.description == "Desc"


def test_basetype_create():
    MyBaseType = CustomType.create_type("MyBaseType")

    assert isinstance(MyBaseType._meta, CustomOptions)
    assert MyBaseType._meta.name == "MyBaseType"
    assert MyBaseType._meta.description is None


def test_basetype_create_extra():
    MyBaseType = CustomType.create_type("MyBaseType", name="Base", description="Desc")

    assert isinstance(MyBaseType._meta, CustomOptions)
    assert MyBaseType._meta.name == "Base"
    assert MyBaseType._meta.description == "Desc"
