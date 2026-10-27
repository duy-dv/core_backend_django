"""Dữ liệu đầu vào và đầu ra của API người dùng."""

from rest_framework import serializers

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Trả thông tin người dùng, không bao giờ trả mật khẩu hoặc mã băm."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone_number",
            "role",
            "is_active",
            "is_locked",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class UserMinimalSerializer(serializers.ModelSerializer):
    """Các trường cần để frontend hiển thị lựa chọn người dùng."""

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role")
        read_only_fields = fields


class RegistrationSerializer(serializers.ModelSerializer):
    # Không bỏ khoảng trắng trong mật khẩu vì chúng có thể là ký tự hợp lệ.
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    class Meta:
        model = User
        fields = ("email", "password", "full_name", "phone_number")

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email đã được sử dụng.")
        return value

    def validate(self, attrs):
        # Người đăng ký không được tự gửi role, is_staff hoặc is_superuser.
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "Trường không được phép." for key in unknown})
        return attrs


class UserCreateSerializer(RegistrationSerializer):
    """Chỉ API dành cho admin mới cho phép chọn vai trò khi tạo tài khoản."""

    class Meta(RegistrationSerializer.Meta):
        fields = (*RegistrationSerializer.Meta.fields, "role")


class UserUpdateSerializer(serializers.ModelSerializer):
    """Liệt kê rõ trường được sửa; không cho đổi mật khẩu bằng phép gán thông thường."""

    class Meta:
        model = User
        fields = ("full_name", "phone_number", "role", "is_active", "is_locked")
