import jwt
from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.utils import timezone
from datetime import datetime, timedelta


class TokenManager:
    @staticmethod
    def get_token(exp, payload, token_type="access"):
        # exp = datetime.now().timestamp() + (exp * 60)
        exp = datetime.utcnow() + timedelta(days=7)

        return jwt.encode(
            {"exp": exp, "type": token_type, **payload},
            settings.SECRET_KEY,
            algorithm="HS256"
        )

    @staticmethod
    def decode_token(token):
        try:
            decoded = jwt.decode(
                token, key=settings.SECRET_KEY, algorithms="HS256")
        except jwt.DecodeError as e:
            print(e)
            return None
        except jwt.ExpiredSignatureError as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None
        if datetime.now().timestamp() > decoded["exp"]:
            return None
        return decoded

    @staticmethod
    def get_access(payload):
        return TokenManager.get_token(5, payload)

    @staticmethod
    def get_refresh(payload):
        return TokenManager.get_token(7*24*60, payload, "refresh")


class Authentication:
    def __init__(self, request):
        self.request = request

    @staticmethod
    def authenticate(self):
        data = self.validate_request()
        if not data:
            return None
        return self.get_user(data["user_id"])

    @staticmethod
    def validate_request(self):
        authorization = self.request.headers.get("HTTP_AUTHORIZATION", None)

        if not authorization:
            return None
        token = authorization[7:]
        print("got token::", token)
        decoded_data = TokenManager.decode_token(token)
        if not decoded_data:
            return None
        return decoded_data

    @staticmethod
    def get_user(user_id):
        from user_controller.models import CustomUser
        try:
            user = CustomUser.objects.get(id=user_id)
            return user
        except CustomUser.DoesNotExist:
            return None


class IsAuthenticatedCustom(BasePermission):

    def has_permission(self, request, _):
        # if request.method in SAFE_METHODS:
        try:
            auth_token = request.META.get("HTTP_AUTHORIZATION", None)
            print(auth_token)
        except Exception:
            return False
        if not auth_token:
            return False

        user = TokenManager.decode_token(auth_token[7:])
        if not user:
            return False
        user_id = user.get("user_id")
        if not user_id:
            return False
        user = Authentication.get_user(user_id)
        if not user:
            return False
        request.user = user
        print("yaay::", request.user)
        return True
