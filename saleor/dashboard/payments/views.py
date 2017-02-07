from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ..views import staff_member_required
from ...order.models import Payment
from ..order.forms import PaymentFilterForm


@staff_member_required
def payment_list(request):
    payments = Payment.objects.select_related('order').all().order_by(
        '-created')

    active_status = request.GET.get('status')
    if active_status:
        payments = payments.filter(status=active_status)

    paginator = Paginator(payments, 30)
    page_number = request.GET.get('page') or 1
    try:
        page_number = int(page_number)
    except ValueError:
        raise Http404(pgettext_lazy(
            'Dashboard message related to an payments',
            'Page can not be converted to an int.'))

    try:
        page = paginator.page(page_number)
    except InvalidPage as err:
        raise Http404(pgettext_lazy(
            'Dashboard message related to an payments',
            'Invalid page (%(page_number)s): %(message)s') % {
                          'page_number': page_number, 'message': str(err)})

    form = PaymentFilterForm(request.POST or None,
                             initial={'status': active_status or None})

    ctx = {'payments': page.object_list, 'paginator': paginator,
           'page_obj': page, 'is_paginated': page.has_other_pages(),
           'form': form}
    return TemplateResponse(request, 'dashboard/payments/list.html', ctx)


@staff_member_required
def payment_details(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return TemplateResponse(request, 'dashboard/payments/detail.html',
                            {'payment': payment})
