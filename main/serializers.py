from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Order, Driver, Vehicle, Tracking, Payment, Cargo, Region, AdministrativeUnit, DeliveryConfirmation
from django.contrib.auth import authenticate


class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    phone_number = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")

        user = authenticate(phone_number=phone_number, password=password)  # CustomBackend ishlaydi

        if user is None:
            raise serializers.ValidationError("Telefon raqam yoki parol noto‘g‘ri.")

        data = super().validate(attrs)
        data["phone_number"] = user.phone_number  # Token ichiga phone_number qo‘shamiz
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'age', 'email', 'phone_number', 'role']

    def validate_age(self, value):
        if value < 17 or value > 100:
            raise serializers.ValidationError("Yosh chegarasi 20 dan 100 gacha bo'lishi kerak.")
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    password_confirmation = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'phone_number', 'password', 'password_confirmation']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user



class DriverSerializer(serializers.ModelSerializer):
    carrier = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='carrier'))

    class Meta:
        model = Driver
        fields = ['id', 'carrier', 'license_number', 'license_expiry','license_image', 'experience_years', 'passport_number','passport_image', 'passport_expiry_date', 'is_verified', 'created_at', 'updated_at']
        depth = 1
        read_only_fields = ('is_verified',)
    

class AdminDriverVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['is_verified']


class DeliverySerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(is_verified=False))

    class Meta:
        model = DeliveryConfirmation
        fields = ['order', 'driver', 'is_delivered_by_driver', 'delivered_at', 'receiver', 'is_received_by_receiver', 'received_at', 'dispatcher_notified']

class VehicleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Vehicle
        fields = '__all__'
    

class TrackingSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(is_verified=True))

    class Meta:
        model = Tracking
        fields = ['order', 'driver', 'vehicle', 'current_location', 'status', 'last_updated']

    
class PaymentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Payment
        fields = '__all__'


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'
        depth = 1

    
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class AdministrativeUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdministrativeUnit
        fields = '__all__'
        depth = 1


class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='owner'))
    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "pickup_region",
            "pickup_location",
            "delivery_region",
            "delivery_location",
            "order_status",
            "cargo",
            'loading_time', 
            'unloading_time',
            "created_at",
            "updated_at",
        ]
    
    def validate(self, data):
        """Pickup location va delivery location noto‘g‘ri viloyatga tegishli emasligini tekshiramiz"""
        if data["pickup_location"].region_id != data["pickup_region"].id:
            raise serializers.ValidationError(
                {"pickup_location": "Tuman/shahar noto‘g‘ri viloyatga tegishli."}
            )

        if data["delivery_location"].region_id != data["delivery_region"].id:
            raise serializers.ValidationError(
                {"delivery_location": "Tuman/shahar noto‘g‘ri viloyatga tegishli."}
            )

        return data

    depth = 1