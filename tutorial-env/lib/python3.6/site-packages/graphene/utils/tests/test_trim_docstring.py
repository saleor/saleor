from ..trim_docstring import trim_docstring


def test_trim_docstring():
    class WellDocumentedObject(object):
        """
        This object is very well-documented. It has multiple lines in its
        description.

        Multiple paragraphs too
        """

    assert (
        trim_docstring(WellDocumentedObject.__doc__)
        == "This object is very well-documented. It has multiple lines in its\n"
        "description.\n\nMultiple paragraphs too"
    )

    class UndocumentedObject(object):
        pass

    assert trim_docstring(UndocumentedObject.__doc__) is None
