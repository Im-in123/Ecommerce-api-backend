from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from .models import (
    CustomUser,
    Jwt,
    UserProfile
)
from .serializers import (
    ChangePasswordSerializer,
    CreateUserSerializer,
    CustomUser, LoginSerializer,
    CustomUserSerializer,
    RefreshSerializer, UserActivities, UserActivitiesSerializer,
    UserProfileSerializer, ResetPasswordEmailRequestSerializer, FinalSetNewPasswordSerializer, ChangePasswordSerializer
)
from ecommerce_api.authentication import IsAuthenticatedCustom, Authentication, TokenManager
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from ecommerce_api.utils import CustomPagination, get_query

from django.views.generic import View
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import render
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.http import HttpResponse


def add_user_activity(user, action):
    try:
        UserActivities.objects.create(
            user_id=user.id,
            email=user.email,
            fullname=user.username,
            action=action
        )
    except Exception as e:
        print(e)


class CreateUserView(APIView):
    http_method_names = ["post"]
    # queryset = CustomUser.objects.all()
    serializer_class = CreateUserSerializer
    # permission_classes = (IsAuthenticatedCustom, A)

    def post(self, request):
        valid_request = self.serializer_class(data=request.data)
        valid_request.is_valid(raise_exception=True)
        # user_type = valid_request.validated_data.get("user_type",None)
        try:

            check_email = CustomUser.objects.get(
                email=valid_request.validated_data.get("email", None))
            if check_email:
                return Response(
                    {"error": "User with this email already exist"},
                    status=400
                )
        except CustomUser.DoesNotExist as e:
            print("creating..", e)
            CustomUser.objects._create_user(**valid_request.validated_data)
            return Response(
                {"success": "User created successfully"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print(e)

        # add_user_activity(request.user, "added new user")


class LoginView(APIView):
    http_method_names = ["post"]
    # queryset = CustomUser.objects.all()
    serializer_class = LoginSerializer

    def post(self, request):
        valid_request = self.serializer_class(data=request.data)
        valid_request.is_valid(raise_exception=True)

        user = authenticate(
            username=valid_request.validated_data["email"],
            password=valid_request.validated_data.get("password", None)
        )

        if not user:
            return Response(
                {"error": {"error":'Invalid email or password'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        Jwt.objects.filter(user_id=user.id).delete()
        access = TokenManager.get_access({"user_id": user.id})
        refresh = TokenManager.get_refresh({"user_id": user.id})
        print("access::", access)
        print("refresh::", refresh)
        Jwt.objects.create(
            user_id=user.id, access=access, refresh=refresh
        )

        user.last_login = datetime.now()
        user.save()

        return Response({"access": access, "refresh": refresh})


class RefreshView(APIView):
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refreshv = serializer.validated_data["refresh"]
            print("refresh:::", refreshv)
            active_jwt = Jwt.objects.get(
                refresh=serializer.validated_data["refresh"])
        except Jwt.DoesNotExist:
            print("refresh token not found")
            return Response({"error": "refresh token not found"}, status=400)
        except Exception as e:
            print(e)
        if not TokenManager.decode_token(serializer.validated_data["refresh"]):
            print("token is invalid or expired")
            return Response({"error": "Token is invalid or has expired"})

        access = TokenManager.get_access({"user_id": active_jwt.user.id})
        refresh = TokenManager.get_refresh({"user_id": active_jwt.user.id})
        # print("access:::::", access)
        # print("refresh:::::", refresh)

        active_jwt.access = access
        active_jwt.refresh = refresh
        active_jwt.save()

        return Response({"access": access, "refresh": refresh})


class MeView(APIView):
    permission_classes = (
        IsAuthenticatedCustom,
    )
    serializer_class = UserProfileSerializer

    def get(self, request):
        data = {}
        print("request.user::", request.user)
        try:
            data = self.serializer_class(request.user.user_profile, context={
                                         'request': request}).data
        except Exception:

            data = {
                "user": {
                    "id": request.user.id,
                    "email_verified": request.user.email_verified,
                    "email": request.user.email,
                    "user_type": request.user.user_type,
                    "type_verified": request.user.type_verified
                },
            }
        return Response(data, status=200)


class UserProfileView(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedCustom, )

    def get_queryset(self):
        data = self.request.query_params.dict()
        keyword = data.get("keyword", None)

        return self.queryset

    def patch(self, request):
        print("patch:::", request)
        try:
            request.data._mutable = True
        except:
            pass
        user = request.data.get("user_id", None)
        user_obj = CustomUser.objects.get(id=user)

        prof = user_obj.user_profile
        serializer = self.serializer_class(
            prof, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        data = self.serializer_class(prof, context={'request': request}).data
        return Response(data, status=200)


class UserActivitiesView(ModelViewSet):
    serializer_class = UserActivitiesSerializer
    http_method_names = ["get"]
    queryset = UserActivities.objects.all()
    permission_classes = (IsAuthenticatedCustom, )
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                "fullname", "email", "action"
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results


class UsersView(ModelViewSet):
    serializer_class = CustomUserSerializer
    http_method_names = ["get"]
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticatedCustom, )
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data, is_superuser=False)

        if keyword:
            search_fields = (
                "email", "user_type"
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results


class LogoutView(APIView):
    permission_classes = (IsAuthenticatedCustom, )

    def get(self, request):
        user_id = request.user.id

        Jwt.objects.filter(user_id=user_id).delete()
        print("logout")
        return Response("logged out successfully", status=200)


class ChangePassword(APIView):
    permission_classes = (IsAuthenticatedCustom, )
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        user = request.user
        syspassword = user.password

        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            currentPassword = serializer.validated_data.pop("currentPassword")
            password = serializer.validated_data.pop("password")

            matchcheck = check_password(currentPassword, syspassword)
            if matchcheck:
                user.set_password(password)
                user.save()
                return Response({"success": "Password changed."}, status=201)
            return Response({"error": "passwords dont match."}, status=401)
        except Exception as e:
            print(e)


class VerifyEmail(View):

    def get(self, request):

        token = request.GET.get('token')
        user = TokenManager.decode_token(token)
        if user:
            user.is_verified = True
            user.save()
            try:
                check = CustomUser.objects.all().filter(email=user.email, verified=False)
                for a in check:
                    if a.is_verified == False:
                        pass
                    else:
                        a.is_verified = False
                        a.email = ""
                        a.save()
            except:
                pass

            return HttpResponse('''<body style='background:black;>
                    <p style='color:red'>Account verified successfully!</p>

                    <a href='http://192.168.43.77:3000/' style='color:white; font-size:50px'>Account verified successfully! Login to continue!</a>
                    </body>''', status=200)

        return HttpResponse('''<body style='background:black;>
                    <p style='color:red'>Error, Action link expired!</p>
                    <a href='http://192.168.43.77:3000/' style='color:white; font-size:50px'>Error, Action link expired </a>
                    </body>''', status=200)


class Util:
    @staticmethod
    def send_email(data):
        try:
            email = EmailMessage(
                subject=data['email_subject'],
                body=data['email_body'],
                to=[data['to_email']],
            )
            email.send()
            print("Sent email to:::", data['to_email'])
        except Exception as e:
            print("Util error:::", e)


class RequestPasswordByEmail(APIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        # data = {'request': request, 'data':request.data }
        serializer = self.serializer_class(data=request.data)
        try:
            email = request.data['email']
            if CustomUser.objects.filter(email=email, email_verified=True).exists():
                user = CustomUser.objects.get(email=email, is_verified=True)
                print("password reset request by::::::", user)
                uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                token = PasswordResetTokenGenerator().make_token(user)

                current_site = get_current_site(request=request).domain
                relativeLink = reverse(
                    "password-reset-confirm", kwargs={'uidb64': uidb64, 'token': token})
                absurl = "http://" + current_site + relativeLink
                email_body = "Hi, \n  Use this link to reset your password \n" + \
                    absurl + " Please do not proceed if this was sent to you by mistake!"
                data = {
                    'domain': absurl,
                    "email_body": email_body,
                    'email_subject': "Password Reset",
                    "to_email": user.email
                }

                Util.send_email(data)

            return Response({"success": "We have sent you a link to reset your password"}, status=200)
        except Exception as e:
            print("error password reset:::::", e)
        return Response({"success": "We have have sent you a link to reset your password"}, status=200)


class PasswordTokenCheck(APIView):
    def get(self, request, uidb64, token):
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                context = {
                    "error": "The token aint valid or has expired, please request a new password reset!!!"
                }
                return render(request, "user_controller/dashbase.html", context)

            context = {
                "success": True,
                "message": "Credentials is valid",
                "uidb64": uidb64,
                "token": token
            }
            return render(request, "user_controller/dashbase.html", context)

        except DjangoUnicodeDecodeError as e:
            context = {
                "error": "The token aint valid or has expired , please request a new password reset!!!"
            }
            return render(request, "user_controller/dashbase.html", context)

        except Exception as e:
            print("password token check::::", e)


class FinalSetNewPassword(APIView):
    serializer_class = FinalSetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({"success": True, "message": "Your password has been reset successfully. Go back to login page to continue!!"}, status=200)


class SecondaryEmailVerification(APIView):
    permission_classes = (IsAuthenticatedCustom, )

    def post(self, request):
        user = request.user

        token = TokenManager.get_refresh({"user_id": user.id})

        current_site = get_current_site(request).domain
        relativeLink = reverse("email-verify")
        bearer = f"1bearer{str(token)}"
        absurl = "http://" + current_site + relativeLink + "?token=" + bearer
        email_body = "Hi " + user.username + " Click link below to verify your iHype account n/" + \
            absurl + " Please do not proceed if this was sent to you by mistake!"
        data = {
            'domain': absurl,
            "email_body": email_body,
            'email_subject': "Please verify your email",
            "to_email": user.email
        }
        Util.send_email(data)
        return Response({"success": "User created."}, status=201)
