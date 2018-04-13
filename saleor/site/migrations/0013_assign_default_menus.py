from django.conf import settings
from django.db import migrations


def assign_default_menus(apps, schema_editor):
    Menu = apps.get_model('menu', 'Menu')
    top_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS['top_menu_name'])[0]
    bottom_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS['bottom_menu_name'])[0]
    Site = apps.get_model('sites', 'Site')
    site = Site.objects.get_current()
    site_settings = site.settings
    site_settings.top_menu = top_menu
    site_settings.bottom_menu = bottom_menu
    site_settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_auto_20180405_0854'),
        ('site', '0012_auto_20180405_0757'),
    ]

    operations = [
        migrations.RunPython(assign_default_menus, migrations.RunPython.noop)
    ]
