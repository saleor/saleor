import six

from ..argument import Argument
from ..enum import Enum, PyEnum
from ..field import Field
from ..inputfield import InputField
from ..schema import ObjectType, Schema


def test_enum_construction():
    class RGB(Enum):
        """Description"""

        RED = 1
        GREEN = 2
        BLUE = 3

        @property
        def description(self):
            return "Description {}".format(self.name)

    assert RGB._meta.name == "RGB"
    assert RGB._meta.description == "Description"

    values = RGB._meta.enum.__members__.values()
    assert sorted([v.name for v in values]) == ["BLUE", "GREEN", "RED"]
    assert sorted([v.description for v in values]) == [
        "Description BLUE",
        "Description GREEN",
        "Description RED",
    ]


def test_enum_construction_meta():
    class RGB(Enum):
        class Meta:
            name = "RGBEnum"
            description = "Description"

        RED = 1
        GREEN = 2
        BLUE = 3

    assert RGB._meta.name == "RGBEnum"
    assert RGB._meta.description == "Description"


def test_enum_instance_construction():
    RGB = Enum("RGB", "RED,GREEN,BLUE")

    values = RGB._meta.enum.__members__.values()
    assert sorted([v.name for v in values]) == ["BLUE", "GREEN", "RED"]


def test_enum_from_builtin_enum():
    PyRGB = PyEnum("RGB", "RED,GREEN,BLUE")

    RGB = Enum.from_enum(PyRGB)
    assert RGB._meta.enum == PyRGB
    assert RGB.RED
    assert RGB.GREEN
    assert RGB.BLUE


def test_enum_from_builtin_enum_accepts_lambda_description():
    def custom_description(value):
        if not value:
            return "StarWars Episodes"

        return "New Hope Episode" if value == Episode.NEWHOPE else "Other"

    def custom_deprecation_reason(value):
        return "meh" if value == Episode.NEWHOPE else None

    PyEpisode = PyEnum("PyEpisode", "NEWHOPE,EMPIRE,JEDI")
    Episode = Enum.from_enum(
        PyEpisode,
        description=custom_description,
        deprecation_reason=custom_deprecation_reason,
    )

    class Query(ObjectType):
        foo = Episode()

    schema = Schema(query=Query)

    GraphQLPyEpisode = schema._type_map["PyEpisode"].values

    assert schema._type_map["PyEpisode"].description == "StarWars Episodes"
    assert (
        GraphQLPyEpisode[0].name == "NEWHOPE"
        and GraphQLPyEpisode[0].description == "New Hope Episode"
    )
    assert (
        GraphQLPyEpisode[1].name == "EMPIRE"
        and GraphQLPyEpisode[1].description == "Other"
    )
    assert (
        GraphQLPyEpisode[2].name == "JEDI"
        and GraphQLPyEpisode[2].description == "Other"
    )

    assert (
        GraphQLPyEpisode[0].name == "NEWHOPE"
        and GraphQLPyEpisode[0].deprecation_reason == "meh"
    )
    assert (
        GraphQLPyEpisode[1].name == "EMPIRE"
        and GraphQLPyEpisode[1].deprecation_reason is None
    )
    assert (
        GraphQLPyEpisode[2].name == "JEDI"
        and GraphQLPyEpisode[2].deprecation_reason is None
    )


def test_enum_from_python3_enum_uses_enum_doc():
    if not six.PY3:
        return

    from enum import Enum as PyEnum

    class Color(PyEnum):
        """This is the description"""

        RED = 1
        GREEN = 2
        BLUE = 3

    RGB = Enum.from_enum(Color)
    assert RGB._meta.enum == Color
    assert RGB._meta.description == "This is the description"
    assert RGB
    assert RGB.RED
    assert RGB.GREEN
    assert RGB.BLUE


def test_enum_value_from_class():
    class RGB(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    assert RGB.RED.value == 1
    assert RGB.GREEN.value == 2
    assert RGB.BLUE.value == 3


def test_enum_value_as_unmounted_field():
    class RGB(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    unmounted = RGB()
    unmounted_field = unmounted.Field()
    assert isinstance(unmounted_field, Field)
    assert unmounted_field.type == RGB


def test_enum_value_as_unmounted_inputfield():
    class RGB(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    unmounted = RGB()
    unmounted_field = unmounted.InputField()
    assert isinstance(unmounted_field, InputField)
    assert unmounted_field.type == RGB


def test_enum_value_as_unmounted_argument():
    class RGB(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    unmounted = RGB()
    unmounted_field = unmounted.Argument()
    assert isinstance(unmounted_field, Argument)
    assert unmounted_field.type == RGB


def test_enum_can_be_compared():
    class RGB(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    assert RGB.RED == 1
    assert RGB.GREEN == 2
    assert RGB.BLUE == 3


def test_enum_can_be_initialzied():
    class RGB(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    assert RGB.get(1) == RGB.RED
    assert RGB.get(2) == RGB.GREEN
    assert RGB.get(3) == RGB.BLUE


def test_enum_can_retrieve_members():
    class RGB(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    assert RGB["RED"] == RGB.RED
    assert RGB["GREEN"] == RGB.GREEN
    assert RGB["BLUE"] == RGB.BLUE


def test_enum_to_enum_comparison_should_differ():
    class RGB1(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    class RGB2(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    assert RGB1.RED != RGB2.RED
    assert RGB1.GREEN != RGB2.GREEN
    assert RGB1.BLUE != RGB2.BLUE


def test_enum_skip_meta_from_members():
    class RGB1(Enum):
        class Meta:
            name = "RGB"

        RED = 1
        GREEN = 2
        BLUE = 3

    assert dict(RGB1._meta.enum.__members__) == {
        "RED": RGB1.RED,
        "GREEN": RGB1.GREEN,
        "BLUE": RGB1.BLUE,
    }
