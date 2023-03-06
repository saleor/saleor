from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("product", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(default="", verbose_name="description", blank=True),
        )
    ]
