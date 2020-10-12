from datetime import date

from django.db import migrations


def set_missing_page_publication_date(apps, schema_editor):
    Page = apps.get_model("page", "Page")
    published_page = Page.objects.filter(
        publication_date__isnull=True, is_published=True
    )
    published_page.update(publication_date=date.today())


class Migration(migrations.Migration):
    dependencies = [
        ("page", "0012_auto_20200709_1102"),
    ]
    operations = [
        migrations.RunPython(set_missing_page_publication_date),
    ]
