from rest_framework import serializers
from .models import UserProfile, CustomUser, GenericFileUpload, UserActivities, UserTypes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import AuthenticationFailed


class GenericFileUploadSerializer(serializers.ModelSerializer):

    class Meta:
        model = GenericFileUpload
        fields = "__all__"


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=5, max_length=20)
    user_type = serializers.ChoiceField(UserTypes)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        exclude = ("password", )


class UserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    city = serializers.CharField(required=False, allow_null=True)
    country = serializers.CharField(required=False, allow_null=True)

    profile_picture = serializers.ImageField(read_only=True)

    class Meta:
        model = UserProfile
        fields = "__all__"


class UserActivitiesSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserActivities
        fields = ("__all__")


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        fields = "__all__"


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ['email']


class FinalSetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = "__all__"

    def validate(self, attrs):

        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')
            idd = force_str((urlsafe_base64_decode(uidb64)))
            user = CustomUser.objects.get(id=idd)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed(
                    "The reset link is invalid, if it has already been used request a new one!!", 401)
            user.set_password(password)
            user.save()
            return (user)

        except Exception as e:
            print("Serializer Finalsetnewpassword::::", e)
            raise AuthenticationFailed(
                "The reset link is invalid, if it has already been used request a new one!!", 401)
        return super().validate(attrs)
