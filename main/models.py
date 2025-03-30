from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from time import timezone
# Create your models here.


class User(AbstractUser):
    ROLE_CHOICES = (
        ('dispatcher', 'Dispetcher'),
        ('carrier', 'Yuk tashuvchi'),
        ('owner', 'Yuk egasi'),
    )
    age = models.PositiveIntegerField(default=18)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Avval foydalanuvchini saqlaymiz

        # Role'ga mos keladigan guruhni topamiz
        role_group_map = {
            'dispatcher': 'dispatcher_group',
            'carrier': 'carrier_group',
            'owner': 'owner_group',
        }
        group_name = role_group_map.get(self.role)
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            self.groups.add(group)  # Foydalanuvchini guruhga qo‘shamiz

    def __str__(self):
        return self.username
    

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
    CARGO_TYPES = [
        ('general', 'General Cargo (Umumiy yuk)'),
        ('fragile', 'Fragile Goods (Mo‘rt tovarlar)'),
        ('perishable', 'Perishable Goods (Tez buziladigan mahsulotlar)'),
        ('hazardous', 'Hazardous Materials (Xavfli materiallar)'),
    ]

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

    cargo_type = models.CharField(max_length=20, choices=CARGO_TYPES)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    weight_unit = models.CharField(max_length=15, choices=WEIGHT_UNITS)
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume_unit = models.CharField(max_length=10, choices=VOLUME_UNITS, default='m³')
    special_requirements = models.TextField(null=True, blank=True)
    transport_type = models.CharField(max_length=155)
    placement_method = models.CharField(max_length=155, blank=True, null=True)


    def __str__(self):
        return f"{self.get_cargo_type_display()} ({self.weight} {self.weight_unit})"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Yakunlandi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    pickup_region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="pickup_orders")
    pickup_location = models.ForeignKey(AdministrativeUnit, on_delete=models.PROTECT, related_name="pickup_orders")
    delivery_region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="delivery_orders")
    delivery_location = models.ForeignKey(AdministrativeUnit, on_delete=models.PROTECT, related_name="delivery_orders")
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name="orders") 
    loading_time = models.DateTimeField(null=True, blank=True)   # Yuklash vaqti
    unloading_time = models.DateTimeField(null=True, blank=True) # tushirish vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} ({self.get_order_status_display()})"






class Driver(models.Model):
    carrier = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile")
    
    license_number = models.CharField(max_length=20, unique=True)  # Haydovchilik guvohnomasi raqami
    license_expiry = models.DateField()  # Guvohnomaning amal qilish muddati
    license_image = models.ImageField(upload_to='licenses/', null=True, blank=True)

    experience_years = models.PositiveIntegerField(default=3)  # Tajriba yillari

    passport_number = models.CharField(max_length=20, unique=True)  # Pasport raqami
    passport_issue_date = models.DateField()  # Pasport berilgan sana
    passport_expiry_date = models.DateField(null=True, blank=True)  # Pasport muddati (agar bo‘lsa)
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
    ("crypto", "Kriptovalyuta"),
)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
