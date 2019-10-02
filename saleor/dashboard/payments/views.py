from typing import TYPE_CHECKING

from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse

from ...payment.gateways.braintree.plugin import BraintreeGatewayPlugin
from ...payment.gateways.dummy.plugin import DummyGatewayPlugin
from ...payment.gateways.razorpay.plugin import RazorpayGatewayPlugin
from ...payment.gateways.stripe.plugin import StripeGatewayPlugin
from ..views import staff_member_required

if TYPE_CHECKING:
    from django.http import HttpRequest

GATEWAYS_PLUGINS = [
    BraintreeGatewayPlugin,
    DummyGatewayPlugin,
    RazorpayGatewayPlugin,
    StripeGatewayPlugin,
]


@staff_member_required
@permission_required("extensions.manage_plugins")
def index(request: "HttpRequest") -> TemplateResponse:
    payment_gateways = [gateway.PLUGIN_NAME for gateway in GATEWAYS_PLUGINS]

    ctx = {"payment_gateways": payment_gateways}
    return TemplateResponse(request, "dashboard/payments/index.html", ctx)
