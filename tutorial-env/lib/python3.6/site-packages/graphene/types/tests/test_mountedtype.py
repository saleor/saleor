
from ..field import Field
from ..scalars import String


class CustomField(Field):
    def __init__(self, *args, **kwargs):
        self.metadata = kwargs.pop("metadata", None)
        super(CustomField, self).__init__(*args, **kwargs)


def test_mounted_type():
    unmounted = String()
    mounted = Field.mounted(unmounted)
    assert isinstance(mounted, Field)
    assert mounted.type == String


def test_mounted_type_custom():
    unmounted = String(metadata={"hey": "yo!"})
    mounted = CustomField.mounted(unmounted)
    assert isinstance(mounted, CustomField)
    assert mounted.type == String
    assert mounted.metadata == {"hey": "yo!"}
