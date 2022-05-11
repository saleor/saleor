from django.conf import settings

from ..core.exceptions import ReadOnlyException
from .views import GraphQLView


class ReadOnlyMiddleware:
    ALLOWED_MUTATIONS = [
        "checkoutAddPromoCode",
        "checkoutBillingAddressUpdate",
        "checkoutComplete",
        "checkoutCreate",
        "checkoutCustomerAttach",
        "checkoutCustomerDetach",
        "checkoutEmailUpdate",
        "checkoutLineDelete",
        "checkoutLinesAdd",
        "checkoutLinesUpdate",
        "checkoutRemovePromoCode",
        "checkoutPaymentCreate",
        "checkoutShippingAddressUpdate",
        "checkoutShippingMethodUpdate",
        "tokenCreate",
        "tokenVerify",
        "tokenRefresh",
    ]

    @staticmethod
    def resolve(next_, root, info, **kwargs):
        operation = info.operation.operation
        if operation != "mutation":
            return next_(root, info, **kwargs)

        # Bypass users authenticated with ROOT_EMAIL
        request = info.context
        user = getattr(request, "user", None)
        if user and not user.is_anonymous:
            user_email = user.email
            root_email = getattr(settings, "ROOT_EMAIL", None)
            if root_email and user_email == root_email:
                return next_(root, info, **kwargs)

        # Bypass authenticated app as to create an app, root user is required
        if request.app:
            return next_(root, info, **kwargs)

        for selection in info.operation.selection_set.selections:
            selection_name = str(selection.name.value)
            blocked = selection_name not in ReadOnlyMiddleware.ALLOWED_MUTATIONS
            if blocked:
                raise ReadOnlyException(
                    "Be aware admin pirate! API runs in read-only mode!"
                )
        return next_(root, info, **kwargs)


def process_view(self, request, view_func, *args):
    if hasattr(view_func, "view_class") and issubclass(
        view_func.view_class, GraphQLView
    ):
        request._graphql_view = True


if settings.ENABLE_DEBUG_TOOLBAR:
    import warnings

    try:
        from graphiql_debug_toolbar.middleware import DebugToolbarMiddleware
    except ImportError:
        warnings.warn("The graphiql debug toolbar was not installed.")
    else:
        DebugToolbarMiddleware.process_view = process_view
