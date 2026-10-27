# Được tạo tự động bởi Django 5.2.17 on 2026-09-29 13:13

import django.db.models.deletion
import django.db.models.functions.text
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Định danh duy nhất UUID', primary_key=True, serialize=False)),
                ('email', models.EmailField(db_index=True, max_length=254, unique=True, verbose_name='Địa chỉ Email')),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True, verbose_name='Số điện thoại')),
                ('full_name', models.CharField(max_length=255, verbose_name='Họ và tên')),
                ('is_active', models.BooleanField(default=True, verbose_name='Đang hoạt động')),
                ('role', models.CharField(choices=[('admin', 'Quản trị viên'), ('manager', 'Quản lý'), ('staff', 'Nhân viên')], default='staff', max_length=50, verbose_name='Vai trò')),
                ('is_locked', models.BooleanField(default=False, verbose_name='Đã khóa')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Nhân viên ban quản trị')),
                ('created_by', models.ForeignKey(blank=True, help_text='Người tạo bản ghi', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('updated_by', models.ForeignKey(blank=True, help_text='Người cập nhật bản ghi', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL)),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Người dùng',
                'verbose_name_plural': 'Danh sách người dùng',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExternalIdentity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=30)),
                ('subject', models.CharField(max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='identities', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('email'), name='users_email_ci_unique'),
        ),
        migrations.AddConstraint(
            model_name='externalidentity',
            constraint=models.UniqueConstraint(fields=('provider', 'subject'), name='unique_provider_subject'),
        ),
    ]
