from django.http import SimpleCookie


def readonly_dashboard(application):
    def wrapper(environ, start_response):
        dashboard_url = '/dashboard'
        cookie = SimpleCookie()
        cookie['readonly'] = True
        cookie['readonly']['Path'] = '/'
        redirect_headers = [('Location', dashboard_url)]
        redirect_headers.extend([('Set-Cookie', c.OutputString())
                                 for c in cookie.values()])
        if all((environ.get('PATH_INFO').startswith(dashboard_url),
               environ['REQUEST_METHOD'] == 'POST')):

            start_response('301 Moved Permanently', redirect_headers)
            return []
        return application(environ, start_response)
    return wrapper

