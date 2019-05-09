# coding: utf-8
from ..str_converters import to_camel_case, to_const, to_snake_case


def test_snake_case():
    assert to_snake_case("snakesOnAPlane") == "snakes_on_a_plane"
    assert to_snake_case("SnakesOnAPlane") == "snakes_on_a_plane"
    assert to_snake_case("SnakesOnA_Plane") == "snakes_on_a__plane"
    assert to_snake_case("snakes_on_a_plane") == "snakes_on_a_plane"
    assert to_snake_case("snakes_on_a__plane") == "snakes_on_a__plane"
    assert to_snake_case("IPhoneHysteria") == "i_phone_hysteria"
    assert to_snake_case("iPhoneHysteria") == "i_phone_hysteria"


def test_camel_case():
    assert to_camel_case("snakes_on_a_plane") == "snakesOnAPlane"
    assert to_camel_case("snakes_on_a__plane") == "snakesOnA_Plane"
    assert to_camel_case("i_phone_hysteria") == "iPhoneHysteria"
    assert to_camel_case("field_i18n") == "fieldI18n"


def test_to_const():
    assert to_const('snakes $1. on a "#plane') == "SNAKES_1_ON_A_PLANE"
