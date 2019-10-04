from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...payment.gateways.braintree.plugin import BraintreeGatewayPlugin
from ...payment.gateways.dummy.plugin import DummyGatewayPlugin
from ...payment.gateways.razorpay.plugin import RazorpayGatewayPlugin
from ...payment.gateways.stripe.plugin import StripeGatewayPlugin
from ..views import staff_member_required
from .forms import GatewayConfigurationForm

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


@staff_member_required
@permission_required("extension.manage_plugins")
def configure_payment_gateway(request: HttpRequest, plugin_name: str) -> HttpResponse:
    plugin = None
    for gateway in GATEWAYS_PLUGINS:
        if gateway.PLUGIN_NAME == plugin_name:
            plugin = gateway
            break
    else:
        msg = pgettext_lazy("Dashboard message", "Selected plugin does not exists.")
        messages.error(request, msg)
        return redirect("dashboard:payments-index")

    form = GatewayConfigurationForm(plugin, request.POST or None)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy("Dashboard message", "Payment config succesfully updated")
        messages.success(request, msg)
        return redirect("dashboard:payments-index")

    ctx = {"plugin_name": plugin_name, "config_form": form}
    return TemplateResponse(request, "dashboard/payments/configuration_form.html", ctx)
