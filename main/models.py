import phonenumbers
import random


from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from time import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import RegexValidator
from phonenumbers import parse, is_valid_number, region_code_for_number
from rest_framework.exceptions import ValidationError
from .utils import generate_auth_code
from phonenumbers import parse, NumberParseException, is_valid_number


class User(AbstractUser):
    ROLE_CHOICES = (
        ('dispatcher', 'Dispetcher'),
        ('carrier', 'Yuk tashuvchi'),
        ('owner', 'Yuk egasi'),
    )
    phone_number = PhoneNumberField(unique=True, region='UZ')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    auth_code = models.CharField(max_length=6, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def clean(self):
        from utils import validate_uz_phone_number
        validate_uz_phone_number(self.phone_number)

    def save(self, *args, **kwargs):
        if not self.auth_code:  # Agar auth_code hali bo'sh bo'lsa, uni yaratish
            self.auth_code = generate_auth_code() 

        super().save(*args, **kwargs)  # Foydalanuvchini saqlaymiz

        # Role'ga mos keladigan guruhni topamiz va qo‘shamiz
        role_group_map = {
            'dispatcher': 'dispatcher_group',
            'carrier': 'carrier_group',
            'owner': 'owner_group',
        }
        group_name = role_group_map.get(self.role)
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            self.groups.add(group)

    def __str__(self):
        return f"{self.username}"
    

class Region(models.Model):
    name = models.CharField(max_length=155)

    class Meta:
        verbose_name = "Viloyat"
        verbose_name_plural = "Viloyatlar"

    def __str__(self):
        return f"{self.name.title()} viloyati"


class AdministrativeUnit(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="units")
    name = models.CharField(max_length=155)

    class Meta:
        verbose_name = "Ma'muriy birlik"
        verbose_name_plural = "Ma'muriy birliklar"

    def __str__(self):
        return f"{self.name.title()} ({self.region.name.title()} viloyati)"


class OwnerDispatcher(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    passport_number = models.CharField(max_length=20, unique=True)  # Pasport raqami
    passport_image = models.ImageField(upload_to='passports/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)  # Admin tomonidan tasdiqlanganmi?
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} (Verified: {self.is_verified})"


class Cargo(models.Model):
    PAYMENT_CHOICES = (
    ("card", "Bank Karta"),
    ("e_wallet", "Elektron Hamyon"),
    ("cash money", "naxt pul"),
)
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Yakunlandi'),
        ('cancelled', 'Bekor qilindi'),
    ]
    WEIGHT_UNITS = [
        ('Kg', 'Kilogram'),
        ('T', 'Tons'),
    ]

    VOLUME_UNITS = [
        ('m³', 'Cubic Meter'),
        ('L', 'Liter'),
    ]
    READNIESS_CHOICE = (('ready', "tayyor"),
                        ('not_ready', "tayyormas"))
    
    customer = models.ForeignKey(OwnerDispatcher, on_delete=models.CASCADE, related_name="cargos")

    pickup_region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="pickup_cargos")
    pickup_location = models.ForeignKey(AdministrativeUnit, on_delete=models.PROTECT, related_name="pickup_cargos") # A nuqtadan
    delivery_region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="delivery_cargos")
    delivery_location = models.ForeignKey(AdministrativeUnit, on_delete=models.PROTECT, related_name="delivery_cargos")# B nuqtaga
    cargo_type = models.CharField(max_length=255) # yuk turi (qolda kiritiladi)
    loading_time = models.DateTimeField(null=True, blank=True)   # Yuklash vaqti
    cargo_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    weight = models.DecimalField(max_digits=10, decimal_places=2) #yuk ogirligi
    weight_unit = models.CharField(max_length=15, choices=WEIGHT_UNITS) # tonna, kg
    volume = models.DecimalField(max_digits=10, decimal_places=2) #yuk hajmi
    readiness_choice = models.CharField(max_length=20, choices=READNIESS_CHOICE) #yuk tayyorligi
    readiness = models.TextField(null=True, blank=True) # yuk tayyorligi biror sabab (bahona)
    placement_method = models.CharField(max_length=155) # Yuk yuklash usuli
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    transport_type = models.CharField(max_length=155, help_text="transfort turi misol uchun: Fura") #transport turi (qolda kiritiladi)
    special_requirements = models.TextField(null=True, blank=True) # qoshimcha (qolda kiritiladi)

    def save(self, *args, **kwargs):
        if self.readiness_choice == 'not_ready':
            self.cargo_status = 'pending'     
        if self.cargo_status == 'completed' and not self.delivery_region:
            raise ValidationError("Buyurtma tugallanganda yetkazib berish manzili kiritilishi kerak!")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"cargo's owner {self.customer.user.get_full_name()} ({self.readiness_choice}) "
    


class Driver(models.Model):
    carrier = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile")
    license_number = models.CharField(max_length=20, unique=True)  # Haydovchilik guvohnomasi raqami
    license_image = models.ImageField(upload_to='licenses/', null=True, blank=True)
    passport_number = models.CharField(max_length=20, unique=True)  # Pasport raqami
    passport_image = models.ImageField(upload_to='passports/', null=True, blank=True)

    is_verified = models.BooleanField(default=False)  # Admin tomonidan tasdiqlanganmi?
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.carrier.get_full_name()} - {self.license_number} (Verified: {self.is_verified})"


class DeliveryConfirmation(models.Model):
    cargo = models.OneToOneField(Cargo, on_delete=models.CASCADE, related_name="confirmation")

    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries_made")
    is_delivered_by_driver = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    receiver = models.ForeignKey(OwnerDispatcher, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries_received")
    is_received_by_receiver = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)

    dispatcher_notified = models.BooleanField(default=False)

    def check_delivery_status(self):
        """Agar haydovchi va qabul qiluvchi tasdiqlasa, buyurtmani yakunlanadi"""
        if self.is_delivered_by_driver and self.is_received_by_receiver == True:
            self.delivered_at = timezone.now()
            self.received_at = timezone.now()
            self.cargo.cargo_status = "completed"
            self.cargo.save()
            tracking = Tracking.objects.filter(cargo=self.cargo).first()
            if tracking:
                tracking.status = "delivered"
                tracking.save()

            self.notify_dispatcher()
            self.save()


class Vehicle(models.Model):
    vehicle = models.CharField(max_length=155)
    driver = models.OneToOneField(Driver, on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField()
    plate_number = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    def __str__(self):
        return f"{self.vehicle} - {self.plate_number}"


class Bid(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
    ]
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="bids")
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name="bids")
    propose = models.TextField()
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)  # Haydovchi narx taklif qiladi
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid by {self.driver.carrier.get_full_name()} for {self.cargo}"


class Tracking(models.Model):
    cargo = models.OneToOneField(Cargo, on_delete=models.CASCADE, related_name='tracking')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trackings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trackings')
    current_location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[('pending', 'Kutilmoqda'),('in_transit', 'Yukda'),('delivered', 'Yetkazildi')], default='pending')
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.status == "delivered":
            self.cargo.cargo_status = 'completed'
        elif self.status == "in_transit":
            self.cargo.cargo_status = 'in_progress'
        self.cargo.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Tracking {self.id}: {self.status} at {self.current_location}"
    

class DispatcherOrder(models.Model):
    dispatcher = models.ForeignKey(OwnerDispatcher, on_delete=models.CASCADE, related_name='managed_cargos',)
    cargo = models.OneToOneField(Cargo,  on_delete=models.CASCADE,  related_name='dispatcher_assignment')
    assigned_driver = models.ForeignKey(Driver,  on_delete=models.SET_NULL,  null=True, blank=True,  related_name='assigned_cargos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def assign_driver(self, driver):
        """Haydovchini buyurtmaga tayinlash"""
        if driver.is_verified:  # Haydovchi tasdiqlangan bo‘lishi kerak
            self.assigned_driver = driver
            self.cargo.cargo_status = 'in_progress'
            self.cargo.save()
        else:
            raise ValidationError(f"Haydovchi {driver} tasdiqlanmagan!")
   
    def mark_as_completed(self):
        """Buyurtmani muvaffaqiyatli yakunlash"""
        if self.assigned_driver:  # Faqat tayinlangan haydovchi bo‘lsa yakunlash
            self.cargo.cargo_status = 'completed'
            self.cargo.save()
        else:
            raise ValidationError("Buyurtmaga tayinlangan haydovchi mavjud emas!")


class Payment(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


