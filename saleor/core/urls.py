from django.conf.urls import url
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^style-guide/', views.styleguide, name='styleguide'),
    url(r'^impersonate/(?P<uid>\d+)/', views.impersonate,
        name='impersonate-start'),
    url(r'^impersonate/stop/$', views.stop_impersonate,
        name='impersonate-stop'),
    url(r'^404', views.handle_404, name='handle-404'),
    url(r'^offline$', views.offline, name='offline'),
    url(r'^manifest\.json$', TemplateView.as_view(
        template_name='manifest.json', content_type='application/json')),
    url(r'^serviceworker\.js', TemplateView.as_view(
        template_name="serviceworker.js",
        content_type='application/javascript',
    ), name='serviceworker.js'),
]
