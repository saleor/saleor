from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from saleor.core.utils import get_paginator_items
from saleor.dashboard.views import staff_member_required
from saleor.dashboard.warehouse.forms import WarehouseForm
from saleor.warehouse.models import Warehouse

if TYPE_CHECKING:
    from uuid import UUID
    from django.http import HttpRequest, HttpResponse


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def index(request: "HttpRequest"):
    warehouses_qs = Warehouse.objects.all()
    warehouses = get_paginator_items(
        warehouses_qs, settings.DASHBOARD_PAGINATE_BY, request.GET.get("page")
    )
    ctx = {"warehouses": warehouses}
    return TemplateResponse(request, "dashboard/warehouse/list.html", ctx)


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def warehouse_create(request: "HttpRequest") -> "HttpResponse":
    form = WarehouseForm(request.POST or None)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy("Dashboard message", "Warehouse created")
        messages.success(request, msg)
        return redirect("dashboard:warehouse-index")
    ctx = {"form": form}
    return TemplateResponse(request, "dashboard/warehouse/form.html", ctx)


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def warehouse_update(request: "HttpRequest", uuid: "UUID") -> "HttpResponse":
    warehouse = get_object_or_404(Warehouse, pk=uuid)
    form = WarehouseForm(request.POST or None, instance=warehouse)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy("Dashboard message", "Warehouse updated")
        messages.success(request, msg)
        return redirect("dashboard:warehouse-index")
    ctx = {"warehouse": warehouse, "form": form}
    return TemplateResponse(request, "dashboard/warehouse/form.html", ctx)


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def warehouse_delete(request: "HttpRequest", uuid: "UUID") -> "HttpResponse":
    warehouse = get_object_or_404(Warehouse, pk=uuid)
    warehouse.delete()
    msg = pgettext_lazy("Dashboard message", "Warehouse deleted")
    messages.success(request, msg)
    return redirect("dashboard-warehouse-index")
