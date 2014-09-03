from django.core.urlresolvers import reverse


class MenuItem(object):
    def __init__(self, verbose_name, regex, view_func, url_name=None):
        self.verbose_name = verbose_name
        self.regex = regex
        self.view_func = view_func
        self.url_name = url_name

    def __str__(self):
        return self.verbose_name

    def get_absolute_url(self):
        return reverse('dashboard:%s' % self.url_name)


class Menu(object):
    items = []

    def __init__(self, items):
        self.items = items

    @property
    def urls(self):
        from django.conf.urls import patterns, url
        urlpatterns = patterns('')
        for item in self.items:
            urlpatterns += patterns('',
                url(item.regex, item.view_func, name=item.url_name)
            )
        return urlpatterns
