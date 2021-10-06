# from graphql.utilities import print_type

from .celeryconf import app as celery_app

__all__ = ["celery_app"]
__version__ = "dev"


# def patched_print_object(type):
#     interfaces = type.interfaces
#     implemented_interfaces = (
#         " implements {}".format(" & ".join(i.name for i in interfaces))
#         if interfaces
#         else ""
#     )

#     return print_type(type)
