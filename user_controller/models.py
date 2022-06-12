from django.db import models
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

UserTypes = (("sales", "sales"),
             ("shopper", "shopper"))

# import datetime
# from django.conf import settings
# from django.utils.timezone import make_aware
# naive_datetime = datetime.datetime.now()
# naive_datetime.tzinfo #None
# settings.TIME_ZONE #'UTC'
# aware_datetime= make_aware(naive_datetime)
# aware_datetime.tzinfo #<UTC
######
# from django.utils import timezone
# import datetime
# datetime.datetime.now(tz= timezone.utc)


class GenericFileUpload(models.Model):
    file_upload = models.FileField(upload_to='profile_image')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_upload}"


class CustomUserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email field is required")

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    user_type = models.CharField(
        max_length=100, choices=UserTypes, default=UserTypes[1])
    type_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_online = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        ordering = ("created_at",)


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, related_name="user_profile", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, null=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True)  # validators should be a list
    national_number = models.CharField(
        max_length=15, blank=True, null=True,)
    calling_code = models.CharField(
        max_length=10, blank=True, null=True, )
    short_country = models.CharField(
        max_length=10, blank=True, null=True,)
    country = models.CharField(
        max_length=50, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics", blank=True, null=True, default='default.jpg')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    class Meta:
        ordering = ("created_at",)


class UserActivities(models.Model):
    user = models.ForeignKey(
        CustomUser, related_name="user_activities", null=True, on_delete=models.SET_NULL)
    email = models.EmailField()
    fullname = models.CharField(max_length=255)
    action = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", )

    def __str__(self):
        return f"{self.fullname} {self.action} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Jwt(models.Model):
    user = models.OneToOneField(
        CustomUser, related_name="login_user", on_delete=models.CASCADE)
    access = models.TextField()
    refresh = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
