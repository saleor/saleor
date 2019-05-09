from pytest import raises

from graphene import ObjectType, String

from ..module_loading import import_string, lazy_import


def test_import_string():
    MyString = import_string("graphene.String")
    assert MyString == String

    MyObjectTypeMeta = import_string("graphene.ObjectType", "__doc__")
    assert MyObjectTypeMeta == ObjectType.__doc__


def test_import_string_module():
    with raises(Exception) as exc_info:
        import_string("graphenea")

    assert str(exc_info.value) == "graphenea doesn't look like a module path"


def test_import_string_class():
    with raises(Exception) as exc_info:
        import_string("graphene.Stringa")

    assert (
        str(exc_info.value)
        == 'Module "graphene" does not define a "Stringa" attribute/class'
    )


def test_import_string_attributes():
    with raises(Exception) as exc_info:
        import_string("graphene.String", "length")

    assert (
        str(exc_info.value)
        == 'Module "graphene" does not define a "length" attribute inside attribute/class '
        '"String"'
    )

    with raises(Exception) as exc_info:
        import_string("graphene.ObjectType", "__class__.length")

    assert (
        str(exc_info.value)
        == 'Module "graphene" does not define a "__class__.length" attribute inside '
        'attribute/class "ObjectType"'
    )

    with raises(Exception) as exc_info:
        import_string("graphene.ObjectType", "__classa__.__base__")

    assert (
        str(exc_info.value)
        == 'Module "graphene" does not define a "__classa__" attribute inside attribute/class '
        '"ObjectType"'
    )


def test_lazy_import():
    f = lazy_import("graphene.String")
    MyString = f()
    assert MyString == String

    f = lazy_import("graphene.ObjectType", "__doc__")
    MyObjectTypeMeta = f()
    assert MyObjectTypeMeta == ObjectType.__doc__
