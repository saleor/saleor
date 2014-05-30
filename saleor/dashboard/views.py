from django.views.generic import ListView, DetailView
from django.template.response import TemplateResponse
from ..order.models import Order


def index(request):
    return TemplateResponse(request, 'dashboard/index.html')


# def orders(request):
#     orders = Order.objects.all()
#     return TemplateResponse(request, 'dashboard/orders.html',
#                             {'orders': orders})


class OrderListView(ListView):
    template_name = 'dashboard/orders/list.html'
    paginate_by = 20
    model = Order


class OrderDetails(DetailView):
    model = Order
    template_name = 'dashboard/orders/detail.html'
    context_object_name = 'order'


orders = OrderListView.as_view()
order_details = OrderDetails.as_view()
