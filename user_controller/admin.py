from django.contrib import admin
from .models import CustomUser, Jwt,   UserProfile, GenericFileUpload


admin.site.register((CustomUser, Jwt, ))
admin.site.register(UserProfile)
admin.site.register(GenericFileUpload)
