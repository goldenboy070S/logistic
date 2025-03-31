import phonenumbers


from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from time import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import RegexValidator
from phonenumbers import parse, is_valid_number, region_code_for_number
from django.core.exceptions import ValidationError
# Create your models here.

PRIORITY_COUNTRIES = [
    ('+1', 'AQSh'),
    ('+44', 'Buyuk Britaniya'),
    ('+33', 'Fransiya'),
    ('+49', 'Germaniya'),
    ('+81', 'Yaponiya'),
    ('+86', 'Xitoy'),
    ('+7', 'Rossiya'),
    ('+82', 'Janubiy Koreya'),
    ('+90', 'Turkiya'),
    ('+998', 'O‘zbekiston'),  # Asosiy davlat
    ('+7', 'Qozog‘iston'),
    ('+996', 'Qirg‘iziston'),
    ('+992', 'Tojikiston'),
    ('+993', 'Turkmaniston'),
    ('+374', 'Armaniston'),
    ('+994', 'Ozarbayjon'),
    ('+995', 'Gruziya'),
    ('+971', 'BAA'),
    ('+966', 'Saudiya Arabistoni'),]

# 🔹 Qolgan barcha davlatlarni alfavit bo‘yicha tartiblaymiz
OTHER_COUNTRIES = sorted(
    [(f"+{code}", f"{phonenumbers.region_code_for_country_code(code)} (+{code})")
     for code in phonenumbers.COUNTRY_CODE_TO_REGION_CODE.keys()
     if f"+{code}" not in dict(PRIORITY_COUNTRIES)],  # Boshidagilarni yana qo‘shmaslik
    key=lambda x: x[1]
)

COUNTRY_CHOICES = PRIORITY_COUNTRIES + OTHER_COUNTRIES


class User(AbstractUser):
    ROLE_CHOICES = (
        ('dispatcher', 'Dispetcher'),
        ('carrier', 'Yuk tashuvchi'),
        ('owner', 'Yuk egasi'),
    )
    country_code = models.CharField(max_length=5, choices=COUNTRY_CHOICES, default='+998')
    phone_number = PhoneNumberField(unique=True, region=None)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """ Country code va phone number bir-biriga mosligini tekshiramiz """
        if self.phone_number:
            parsed_number = phonenumbers.parse(str(self.phone_number), None)
            expected_country_code = self.country_code.replace('+', '')  # "+998" → "998"

            if str(parsed_number.country_code) != expected_country_code:
                raise ValidationError({'phone_number': f"Telefon raqam {self.get_country_code_display()} uchun noto‘g‘ri!"})


    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.first_name

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



class Cargo(models.Model):
    WEIGHT_UNITS = [
        ("Lb", "Pound"),
        ('Kg', 'Kilogram'),
        ('G', 'Gram'),
        ('T', 'Tons'),
    ]

    VOLUME_UNITS = [
        ('m³', 'Cubic Meter'),
        ('L', 'Liter'),
    ]

    READNIESS_CHOICE = (('ready', "tayyor"),
                        ('not_ready', "tayyormas"))
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cargos")

    cargo_type = models.CharField(max_length=255) # yuk turi (qolda kiritiladi)
    weight = models.DecimalField(max_digits=10, decimal_places=2) #yuk ogirligi
    weight_unit = models.CharField(max_length=15, choices=WEIGHT_UNITS) # tonna, kg
    volume = models.DecimalField(max_digits=10, decimal_places=2) #yuk hajmi
    volume_unit = models.CharField(max_length=10, choices=VOLUME_UNITS, default='m³') # m³ kub
    special_requirements = models.TextField(null=True, blank=True) # qoshimcha (qolda kiritiladi)
    readiness_choice = models.CharField(max_length=20, choices=READNIESS_CHOICE, null=True, blank=True) #yuk tayyorligi
    readiness = models.TextField(null=True, blank=True) # yuk tayyorligi biror sabab (bahona)
    transport_type = models.CharField(max_length=155, help_text="transfort turi misol uchun: Fura") #transport turi (qolda kiritiladi)
    placement_method = models.CharField(max_length=155) # Yuk yuklash usuli


    def __str__(self):
        return f" ({self.weight} {self.weight_unit})"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Yakunlandi'),
        ('cancelled', 'Bekor qilindi'),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    pickup_region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="pickup_orders")
    pickup_location = models.ForeignKey(AdministrativeUnit, on_delete=models.PROTECT, related_name="pickup_orders") # A nuqtadan
    delivery_region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="delivery_orders")
    delivery_location = models.ForeignKey(AdministrativeUnit, on_delete=models.PROTECT, related_name="delivery_orders")# B nuqtaga
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name="orders") 
    loading_time = models.DateTimeField(null=True, blank=True)   # Yuklash vaqti
    unloading_time = models.DateTimeField(null=True, blank=True) # tushirish vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} )"
    

class Owner_dispatcher(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    passport_number = models.CharField(max_length=20, unique=True)  # Pasport raqami
    passport_image = models.ImageField(upload_to='passports/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)  # Admin tomonidan tasdiqlanganmi?
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name}, {self.user.last_name} Verified: {self.is_verified})"


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
        return f"{self.carrier} - {self.license_number} (Verified: {self.is_verified})"


class DeliveryConfirmation(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="confirmation")

    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries_made")
    is_delivered_by_driver = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries_received")
    is_received_by_receiver = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)

    dispatcher_notified = models.BooleanField(default=False)

    def check_delivery_status(self):
        """Agar haydovchi va qabul qiluvchi tasdiqlasa, buyurtmani yakunlaymiz"""
        if self.is_delivered_by_driver and self.is_received_by_receiver:
            self.delivered_at = timezone.now()
            self.received_at = timezone.now()
            self.order.order_status = "completed"
            self.order.save()
            
            # ✅ Yuk yetkazib berildi, Tracking log qo‘shamiz
            Tracking.objects.create(
                order=self.order,
                status="delivered",
                location=self.order.delivery_location.name  # Manzilni yozamiz
            )
            
            self.notify_dispatcher()
            self.save()

    def notify_dispatcher(self):
        """Dispatcherga bildirish yuborish"""
        if not self.dispatcher_notified:
            print(f"🚚 Buyurtma #{self.order.id} yetib keldi. Dispatcher xabardor qilindi.")
            self.dispatcher_notified = True
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


class Tracking(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='tracking')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trackings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trackings')
    current_location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('in_transit', 'In Transit'), ('delivered', 'Delivered')], default='pending')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tracking {self.id}: {self.status} at {self.current_location}"


class Payment(models.Model):
    PAYMENT_CHOICES = (
    ("card", "Bank Karta"),
    ("e_wallet", "Elektron Hamyon"),
    ("cash money", "naxt pul"),
)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
