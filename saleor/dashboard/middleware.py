from .views import dashboard


class DashboardMiddleware(object):
    def process_request(self, request):
        setattr(request, 'dashboard', dashboard)
