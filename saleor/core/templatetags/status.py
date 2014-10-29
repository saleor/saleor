from django.template import Library

register = Library()


ERRORS = ['error', 'reject', 'rejected']
SUCCESSES = ['accept', 'confirmed', 'fully-paid', 'shipped', 'refunded']


@register.inclusion_tag('status_label.html')
def render_status(status, status_display=None):
    if status in ERRORS:
        label_cls = 'danger'
    elif status in SUCCESSES:
        label_cls = 'success'
    else:
        label_cls = 'default'
    return {'label_cls': label_cls, 'status': status_display or status}
