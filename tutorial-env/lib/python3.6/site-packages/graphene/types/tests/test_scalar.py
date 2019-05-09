
from ..scalars import Scalar


def test_scalar():
    class JSONScalar(Scalar):
        """Documentation"""

    assert JSONScalar._meta.name == "JSONScalar"
    assert JSONScalar._meta.description == "Documentation"
