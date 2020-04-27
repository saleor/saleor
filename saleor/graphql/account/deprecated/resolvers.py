from ....app.models import App


def resolve_service_accounts(info, **_kwargs):
    return App.objects.all()
