from django.template import Library

register = Library()


def request_summary(silk_request):
    return {'silk_request': silk_request}


def request_menu(request, silk_request):
    return {'request': request,
            'silk_request': silk_request}


def root_menu(request):
    return {'request': request}


def profile_menu(request, profile, silk_request=None):
    context = {'request': request, 'profile': profile}
    if silk_request:
        context['silk_request'] = silk_request
    return context


def profile_summary(profile):
    return {'profile': profile}


def heading(text):
    return {'text': text}


def code(lines, actual_line):
    return {'code': lines, 'actual_line': [x.strip() for x in actual_line]}


register.inclusion_tag('silk/inclusion/request_summary.html')(request_summary)
register.inclusion_tag('silk/inclusion/profile_summary.html')(profile_summary)
register.inclusion_tag('silk/inclusion/code.html')(code)
register.inclusion_tag('silk/inclusion/request_menu.html')(request_menu)
register.inclusion_tag('silk/inclusion/profile_menu.html')(profile_menu)
register.inclusion_tag('silk/inclusion/root_menu.html')(root_menu)
register.inclusion_tag('silk/inclusion/heading.html')(heading)
