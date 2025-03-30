from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Order, Driver, Tracking, Vehicle, Payment, Cargo, Region, AdministrativeUnit, DeliveryConfirmation
from django.utils.translation import gettext_lazy as _
# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'first_name', 'last_name', 'email', 'age', 'phone_number', 'role'] 
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    def get_fieldsets(self, request, obj=None):
        """
        Foydalanuvchini qo‘shish jarayonini bosqichma-bosqich qilish.
        """
        if not obj:  # Agar foydalanuvchi yaratish jarayoni bo‘lsa
            return (
                (_("Step 1: Login Info"), {'fields': ('username', 'phone_number', 'password1', 'password2')}),
                (_("Step 2: Personal Info"), {'fields': ('first_name', 'last_name', 'email', 'age', 'role')}),
            )
        return super().get_fieldsets(request, obj)

    fieldsets = (
        (None, {'fields': ('username', 'phone_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'age', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


class DriverAdmin(admin.ModelAdmin):
    list_display = ('carrier', 'license_number', 'experience_years', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('carrier__username', 'license_number', 'passport_number')
    actions = ['verify_drivers']

    @admin.action(description="Haydovchini tasdiqlash")
    def verify_drivers(self, request, queryset):
        queryset.update(is_verified=True)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "driver":
            kwargs["queryset"] = User.objects.filter(role="carrier")  
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OrderAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "costomer":
            kwargs["queryset"] = User.objects.filter(role="owner")  
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

class DeliveryAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "driver":
            kwargs["queryset"] = User.objects.filter(is_verified=False)  
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TrackingAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "driver":
            kwargs["queryset"] = User.objects.filter(is_verified=True)  
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

admin.site.register(User, CustomUserAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(DeliveryConfirmation, DeliveryAdmin)    
admin.site.register(Order, OrderAdmin)
admin.site.register(Tracking, TrackingAdmin)
admin.site.register(Payment)
admin.site.register(Vehicle)
admin.site.register(Cargo)
admin.site.register(AdministrativeUnit)
admin.site.register(Region)