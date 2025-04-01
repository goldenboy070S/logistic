from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Order, Driver, Tracking, Vehicle, Payment, Cargo, Region, AdministrativeUnit, DeliveryConfirmation, OwnerDispatcher, DispatcherOrder, DriverAdvertisement
from django.utils.translation import gettext_lazy as _
# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'first_name', 'last_name', 'phone_number', 'role'] 
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)


    fieldsets = (
        (_("🔹 Login ma'lumotlari"), {'fields': ('phone_number', 'password')}),
        (_("🔹 Shaxsiy ma'lumotlar"), {'fields': ('first_name', 'last_name', 'role')}),
        (_("🔹 Ruxsatlar"), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_("🔹 Muhim sanalar"), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (  # Yangi foydalanuvchi qo‘shish uchun maydonlar
        (None, {
            'classes': ('wide',),
            'fields': ('country_code', 'phone_number', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )
    

class DriverAdmin(admin.ModelAdmin):
    list_display = ('carrier', 'license_number', 'is_verified')
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


class OwnerDispatcherAdmin(admin.ModelAdmin):
    list_display = ('user', 'passport_number', 'is_verified')  # Ko‘rinadigan maydonlar
    list_filter = ('is_verified',)  # Filter qilish imkoniyati
    search_fields = ('user__username', 'passport_number')  # Qidirish imkoniyati
    actions = ['verify_owners_dispatchers']  # Action tugmasi

    @admin.action(description="Owner va Dispatcherni tasdiqlash")
    def verify_owners_dispatchers(self, request, queryset):
        queryset.update(is_verified=True)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(role__in=["owner", "dispatcher"])  
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OrderAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "owner":
            kwargs["queryset"] = OwnerDispatcher.objects.filter(role="owner", is_verified=True)  
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

class DeliveryAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "driver":
            kwargs["queryset"] = Driver.objects.filter(is_verified=True)  
        if db_field.name == "receiver":
            kwargs["queryset"] = OwnerDispatcher.objects.filter(user__role="owner", is_verified=True)  # Bu yerda qidiriladigan foydalanuvchilarni o'qib ko’ring 
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TrackingAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "driver":
            kwargs["queryset"] = Driver.objects.filter(is_verified=True) 
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CargoAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer":
            kwargs["queryset"] = User.objects.filter(role="owner", is_verified=True)  
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class DispatcherOrderAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_driver":
            kwargs["queryset"] = Driver.objects.filter(is_verified=True)  
        if db_field.name == "dispatcher":
            kwargs["queryset"] = OwnerDispatcher.objects.filter(user__role="dispatcher", is_verified=True)  # Bu yerda qidiriladigan foydalanuvchilarni o'qib ko’ring 
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(OwnerDispatcher, OwnerDispatcherAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(DeliveryConfirmation, DeliveryAdmin)    
admin.site.register(Order, OrderAdmin)
admin.site.register(DispatcherOrder, DispatcherOrderAdmin)
admin.site.register(Tracking, TrackingAdmin)
admin.site.register(Payment)
admin.site.register(Vehicle)
admin.site.register(Cargo, CargoAdmin)
admin.site.register(AdministrativeUnit)
admin.site.register(Region)