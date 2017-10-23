from celery import shared_task
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.template.loader import get_template
from weasyprint import CSS, HTML


INVOICE_TEMPLATE = 'dashboard/order/pdf/invoice.html'
PACKING_SLIP_TEMPLATE = 'dashboard/order/pdf/packing_slip.html'


def _create_pdf(rendered_template, request):
    stylesheet = [CSS(
        url=request.build_absolute_uri(static('/assets/document.css')))]
    pdf_file = (HTML(string=rendered_template)
                .write_pdf(stylesheets=stylesheet))
    return pdf_file


@shared_task
def create_packing_slip_pdf(group, order, request):
    ctx = {'order': order, 'group': group,
           'logo_uri': request.build_absolute_uri(
               static('/images/saleor_logo_black.svg'))}
    rendered_template = get_template(PACKING_SLIP_TEMPLATE).render(ctx)
    pdf_file = _create_pdf(rendered_template, request)
    return pdf_file


@shared_task
def create_invoice_pdf(group, order, request):
    ctx = {'order': order, 'group': group,
           'logo_uri': request.build_absolute_uri(
               static('/images/saleor_logo_black.svg'))}
    rendered_template = get_template(INVOICE_TEMPLATE).render(ctx)
    pdf_file = _create_pdf(rendered_template, request)
    return pdf_file
