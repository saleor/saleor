import re

from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils import timezone
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = Library()


def _no_op(x):
    return x


def _esc_func(autoescape):
    if autoescape:
        return conditional_escape
    return _no_op


@stringfilter
def spacify(value, autoescape=None):
    esc = _esc_func(autoescape)
    val = esc(value).replace(' ', "&nbsp;")
    val = val.replace('\t', '    ')
    return mark_safe(val)


def _urlify(str):
    r = re.compile('"(?P<src>.*\.py)", line (?P<num>[0-9]+).*')
    m = r.search(str)
    while m:
        group = m.groupdict()
        src = group['src']
        num = group['num']
        start = m.start('src')
        end = m.end('src')
        rep = '<a href="/silk/src/?file_path={src}&line_num={num}">{src}</a>'.format(src=src, num=num)
        str = str[:start] + rep + str[end:]
        m = r.search(str)
    return str


@register.filter
def hash(h, key):
    return h[key]


def _process_microseconds(dt_strftime):
    splt = dt_strftime.split('.')
    micro = splt[-1]
    time = '.'.join(splt[0:-1])
    micro = '%.3f' % float('0.' + micro)
    return time + micro[1:]


def _silk_date_time(dt):
    today = timezone.now().date()
    if dt.date() == today:
        dt_strftime = dt.strftime('%H:%M:%S.%f')
        return _process_microseconds(dt_strftime)
    else:
        return _process_microseconds(dt.strftime('%Y.%m.%d %H:%M.%f'))


@register.filter(expects_localtime=True)
def silk_date_time(dt):
    return _silk_date_time(dt)


@register.filter
def sorted(l):
    return sorted(l)


@stringfilter
def filepath_urlify(value, autoescape=None):
    value = _urlify(value)
    return mark_safe(value)


@stringfilter
def body_filter(value):
    print(value)
    if len(value) > 20:
        return 'Too big!'
    else:
        return value


spacify.needs_autoescape = True
filepath_urlify.needs_autoescape = True
register.filter(spacify)
register.filter(filepath_urlify)
register.filter(body_filter)
