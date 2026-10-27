# Được tạo tự động bởi Django 5.2.17 on 2026-09-29 13:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ExternalIdentity',
        ),
    ]
