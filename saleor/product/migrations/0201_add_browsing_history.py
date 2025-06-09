from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('product', '0200_merge_20250527_1210'),
        ('account', '0087_alter_address_metadata_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductBrowsingHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, help_text='Anonymous user's session key', max_length=40, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('product', models.ForeignKey(help_text='Products viewed', on_delete=django.db.models.deletion.CASCADE, to='product.product')),
                ('user', models.ForeignKey(blank=True, help_text='Logged in user, null for anonymous users', null=True, on_delete=django.db.models.deletion.CASCADE, to='account.user')),
            ],
            options={
                'db_table': 'product_browsing_history',
            },
        ),
        migrations.AddIndex(
            model_name='productbrowsinghistory',
            index=models.Index(fields=['user', '-created_at'], name='product_br_user_id_e9c4d7_idx'),
        ),
        migrations.AddIndex(
            model_name='productbrowsinghistory',
            index=models.Index(fields=['session_key', '-created_at'], name='product_br_session_a08f3b_idx'),
        ),
        migrations.AddIndex(
            model_name='productbrowsinghistory',
            index=models.Index(fields=['product', '-created_at'], name='product_br_product_6b9c8d_idx'),
        ),
        migrations.AddConstraint(
            model_name='productbrowsinghistory',
            constraint=models.UniqueConstraint(condition=models.Q(('user__isnull', False)), fields=('user', 'product'), name='unique_user_product_browsing'),
        ),
        migrations.AddConstraint(
            model_name='productbrowsinghistory',
            constraint=models.UniqueConstraint(condition=models.Q(('session_key__isnull', False)), fields=('session_key', 'product'), name='unique_session_product_browsing'),
        ),
    ]