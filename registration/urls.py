from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^login/$', 'registration.views.login', name='login'),
    url(r'^logout/$', 'registration.views.logout', name='logout'),
    url(r'^register/$', 'registration.views.register', name='register'),
)
