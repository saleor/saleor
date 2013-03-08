from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^login/$', 'registration.views.login', name='login'),
    url(r'^logout/$', 'registration.views.logout', name='logout'),
    url(r'^register/$', 'registration.views.register', name='register'),
    url(r'^oauth_callback/$', 'registration.views.oauth_callback',
        name='oauth_callback'),
    url(r'^confirm_email/$', 'registration.views.confirm_email',
        name='confirm_email'),
)
