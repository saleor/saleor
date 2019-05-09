from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('refresh_token', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='refreshtoken',
            options={'verbose_name': 'refresh token', 'verbose_name_plural': 'refresh tokens'},
        ),
    ]
