from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...warehouse.models import Warehouse
from ..views import staff_member_required
from .forms import WarehouseAddressForm, WarehouseForm, save_warehouse_from_forms

if TYPE_CHECKING:
    from uuid import UUID
    from django.http import HttpRequest, HttpResponse


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def index(request: "HttpRequest") -> "HttpResponse":
    warehouses_qs = Warehouse.objects.prefetch_data()
    warehouses = get_paginator_items(
        warehouses_qs, settings.DASHBOARD_PAGINATE_BY, request.GET.get("page")
    )
    ctx = {"warehouses": warehouses, "is_empty": not warehouses_qs.exists()}
    return TemplateResponse(request, "dashboard/warehouse/list.html", ctx)


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def warehouse_create(request: "HttpRequest") -> "HttpResponse":
    warehouse_form = WarehouseForm(request.POST or None)
    address_form = WarehouseAddressForm(request.POST or None)
    if address_form.is_valid() and warehouse_form.is_valid():
        warehouse = save_warehouse_from_forms(warehouse_form, address_form)
        msg = pgettext_lazy("Dashboard message", "Warehouse created")
        messages.success(request, msg)
        return redirect("dashboard:warehouse-detail", uuid=warehouse.id)
    ctx = {"warehouse_form": warehouse_form, "address_form": address_form}
    return TemplateResponse(request, "dashboard/warehouse/form.html", ctx)


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def warehouse_update(request: "HttpRequest", uuid: "UUID") -> "HttpResponse":
    qs = Warehouse.objects.prefetch_data()
    warehouse = get_object_or_404(qs, pk=uuid)
    warehouse_form = WarehouseForm(request.POST or None, instance=warehouse)
    address_form = WarehouseAddressForm(
        request.POST or None, instance=warehouse.address
    )
    if address_form.is_valid() and warehouse_form.is_valid():
        save_warehouse_from_forms(warehouse_form, address_form)
        msg = pgettext_lazy("Dashboard message", "Warehouse updated")
        messages.success(request, msg)
        return redirect("dashboard:warehouse-detail", uuid=warehouse.id)
    ctx = {
        "warehouse": warehouse,
        "warehouse_form": warehouse_form,
        "address_form": address_form,
    }
    return TemplateResponse(request, "dashboard/warehouse/form.html", ctx)


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def warehouse(request: "HttpRequest", uuid: "UUID") -> "HttpResponse":
    qs = Warehouse.objects.prefetch_data()
    ctx = {"warehouse": get_object_or_404(qs, pk=uuid)}
    return TemplateResponse(request, "dashboard/warehouse/detail.html", ctx)


@staff_member_required
@permission_required("warehouse.manage_warehouses")
def warehouse_delete(request: "HttpRequest", uuid: "UUID") -> "HttpResponse":
    warehouse = get_object_or_404(Warehouse, pk=uuid)
    if request.method == "POST":
        warehouse.delete()
        msg = pgettext_lazy("Dashboard message", "Warehouse deleted")
        messages.success(request, msg)
        return redirect("dashboard:warehouse-list")
    ctx = {"warehouse": warehouse}
    return TemplateResponse(
        request, "dashboard/warehouse/modal/confirm_delete.html", ctx
    )
