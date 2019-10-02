from typing import TYPE_CHECKING

from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse

from ..views import staff_member_required

if TYPE_CHECKING:
    from django.http import HttpRequest


@staff_member_required
@permission_required("extensions.manage_plugins")
def index(request: "HttpRequest") -> TemplateResponse:
    ctx = {}
    return TemplateResponse(request, "dashboard/payments/index.html", ctx)
