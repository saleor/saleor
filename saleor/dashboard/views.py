from django.contrib.auth.decorators import user_passes_test
from django.views.generic import ListView, DetailView
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from ..order.models import Order
from menu import Menu, MenuItem


def index(request):
    return TemplateResponse(request, 'dashboard/index.html')


class StaffMemberOnlyMixin(object):
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(StaffMemberOnlyMixin, self).dispatch(*args, **kwargs)


class OrderListView(StaffMemberOnlyMixin, ListView):
    template_name = 'dashboard/orders/list.html'
    paginate_by = 20
    model = Order

    def get_queryset(self):
        queryset = super(OrderListView, self).get_queryset()
        if 'status' in self.request.GET:
            queryset = queryset.filter(status=self.request.GET['status'])
        return queryset

    def get_context_data(self, **kwargs):
        context_data = super(OrderListView, self).get_context_data(**kwargs)
        if 'status' in self.request.GET:
            context_data['status_filter'] = self.request.GET['status']
        return context_data


class OrderDetails(StaffMemberOnlyMixin, DetailView):
    model = Order
    template_name = 'dashboard/orders/detail.html'
    context_object_name = 'order'

    def get_delivery_info(self):
        try:
            return self.object.groups.select_subclasses().get()
        except self.model.DoesNotExist:
            return None


orders = OrderListView.as_view()
order_details = OrderDetails.as_view()

dashboard = Menu([
    MenuItem('Index', r'^$', index, url_name='index'),
    MenuItem('Orders', r'^orders/$', orders, url_name='orders')
])
