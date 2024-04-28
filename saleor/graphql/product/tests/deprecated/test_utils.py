from .....plugins.manager import get_plugins_manager
from .....tax.models import TaxClass
from ...mutations.utils import clean_tax_code


def test_clean_tax_code_does_nothing_when_empty_data():
    # given
    manager = get_plugins_manager(allow_replica=False)
    data = {}

    # when
    clean_tax_code(data, manager)

    # then
    assert data == {}


def test_clean_tax_code_does_nothing_when_tax_class_provided():
    # given
    manager = get_plugins_manager(allow_replica=False)
    data = {"tax_code": "P0000000", "tax_class": "VGF4Q2xhc3M6MQ=="}

    # when
    clean_tax_code(data, manager)

    # then
    assert data == {"tax_code": "P0000000", "tax_class": "VGF4Q2xhc3M6MQ=="}


def test_clean_tax_code_when_tax_class_exists_by_name():
    # given
    manager = get_plugins_manager(allow_replica=False)
    tax_code = "P0000000"
    tax_class = TaxClass.objects.create(name=tax_code)
    data = {"tax_code": tax_code}

    # when
    clean_tax_code(data, manager)

    # then
    assert data["tax_class"] == tax_class


def test_clean_tax_code_when_tax_class_exists_by_avatax():
    # given
    manager = get_plugins_manager(allow_replica=False)
    tax_code = "P0000000"
    tax_class = TaxClass.objects.create(name="Test", metadata={"avatax.code": tax_code})
    data = {"tax_code": tax_code}

    # when
    clean_tax_code(data, manager)

    # then
    assert data["tax_class"] == tax_class


def test_clean_tax_code_when_tax_class_exists_by_vatlayer():
    # given
    manager = get_plugins_manager(allow_replica=False)
    tax_code = "P0000000"
    tax_class = TaxClass.objects.create(
        name="Test", metadata={"vatlayer.code": tax_code}
    )
    data = {"tax_code": tax_code}

    # when
    clean_tax_code(data, manager)

    # then
    assert data["tax_class"] == tax_class


def test_clean_tax_code_when_tax_class_does_not_exists():
    # given
    manager = get_plugins_manager(allow_replica=False)
    tax_code = "P0000000"
    TaxClass.objects.all().delete()
    data = {"tax_code": tax_code}

    # when
    clean_tax_code(data, manager)

    # then
    assert data["tax_class"] is None
