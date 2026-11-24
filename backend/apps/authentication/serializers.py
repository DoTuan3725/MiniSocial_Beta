from rest_framework import serializers

from .models import User


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "email_verified", "created_at"]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    full_name = serializers.CharField(max_length=100)
    birth_date = serializers.DateField(required=False, allow_null=True)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OtpRequestSerializer(EmailSerializer):
    purpose = serializers.ChoiceField(choices=["register", "login", "reset"])


class OtpVerifySerializer(EmailSerializer):
    otp = serializers.RegexField(r"^\d{6}$", error_messages={"invalid": "Mã OTP gồm 6 chữ số"})


class LoginSerializer(EmailSerializer):
    password = serializers.CharField(write_only=True)


class ResetPasswordSerializer(OtpVerifySerializer):
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128)
