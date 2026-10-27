# Được tạo tự động bởi Django 5.2.17 on 2026-09-29 13:13

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SampleItem',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Định danh duy nhất UUID', primary_key=True, serialize=False)),
                ('title', models.CharField(db_index=True, max_length=255, verbose_name='Tiêu đề')),
                ('description', models.TextField(blank=True, verbose_name='Mô tả chi tiết')),
                ('status', models.CharField(choices=[('ACTIVE', 'Đang hoạt động'), ('INACTIVE', 'Ngừng hoạt động'), ('ARCHIVED', 'Đã lưu trữ')], db_index=True, default='ACTIVE', max_length=20, verbose_name='Trạng thái')),
                ('priority', models.CharField(choices=[('LOW', 'Thấp'), ('MEDIUM', 'Trung bình'), ('HIGH', 'Cao'), ('CRITICAL', 'Khẩn cấp')], default='MEDIUM', max_length=20, verbose_name='Mức độ ưu tiên')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Dữ liệu mở rộng (JSON)')),
            ],
            options={
                'verbose_name': 'Mục mẫu',
                'verbose_name_plural': 'Danh sách mục mẫu',
                'ordering': ['-created_at'],
            },
        ),
    ]
