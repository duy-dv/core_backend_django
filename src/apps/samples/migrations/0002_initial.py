# Được tạo tự động bởi Django 5.2.17 on 2026-09-29 13:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('samples', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='sampleitem',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='Người tạo bản ghi', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sampleitem',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sample_items', to=settings.AUTH_USER_MODEL, verbose_name='Người phụ trách / Sở hữu'),
        ),
        migrations.AddField(
            model_name='sampleitem',
            name='updated_by',
            field=models.ForeignKey(blank=True, help_text='Người cập nhật bản ghi', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
