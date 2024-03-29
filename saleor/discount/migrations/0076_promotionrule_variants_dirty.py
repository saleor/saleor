# Generated by Django 3.2.23 on 2024-01-09 08:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0075_promotionrule_gifts"),
    ]

    operations = [
        migrations.AddField(
            model_name="promotionrule",
            name="variants_dirty",
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL(
            """
            ALTER TABLE discount_promotionrule
            ALTER COLUMN variants_dirty
            SET DEFAULT false;
            """,
            migrations.RunSQL.noop,
        ),
    ]
