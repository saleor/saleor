import pytest
from django.conf import settings

from ..app.models import App, AppExtension


def test_subqueries_no_allowed_across_different_databases(app_with_extensions):
    replica = settings.DATABASE_CONNECTION_REPLICA_NAME
    writer = settings.DATABASE_CONNECTION_DEFAULT_NAME
    subquery = App.objects.using(replica).all()
    query = AppExtension.objects.using(writer).filter(app_id__in=subquery)

    with pytest.raises(
        ValueError, match="Subqueries aren't allowed across different databases."
    ):
        list(query)
