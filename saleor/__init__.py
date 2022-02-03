from graphql.utils import schema_printer

from .celeryconf import app as celery_app

__all__ = ["celery_app"]
__version__ = "3.1.0-a.25"


def patched_print_object(type):
    interfaces = type.interfaces
    implemented_interfaces = (
        " implements {}".format(" & ".join(i.name for i in interfaces))
        if interfaces
        else ""
    )

    return ("type {}{} {{\n" "{}\n" "}}").format(
        type.name, implemented_interfaces, schema_printer._print_fields(type)
    )
