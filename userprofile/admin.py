from django.contrib import admin
from .models import User, Address


class AddressAdmin(admin.TabularInline):

    model = Address


class UserAdmin(admin.ModelAdmin):

    inlines = [AddressAdmin]


admin.site.register(User, UserAdmin)
