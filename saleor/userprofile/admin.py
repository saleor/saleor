from django.contrib import admin
from .models import User, AddressBook


class AddressAdmin(admin.TabularInline):

    model = AddressBook


class UserAdmin(admin.ModelAdmin):

    inlines = [AddressAdmin]


admin.site.register(User, UserAdmin)
