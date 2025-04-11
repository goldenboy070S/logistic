from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Driver, Vehicle, Tracking, Payment, Cargo, Region, AdministrativeUnit, DeliveryConfirmation, OwnerDispatcher, DispatcherOrder, Bid
from django.contrib.auth import authenticate
from phonenumber_field.serializerfields import PhoneNumberField


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

    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'phone_number', 'role']
        read_only_fields = ['role', 'phone_number']


class PhoneNumberField(serializers.CharField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        from .utils import validate_priority_phone_number
        validate_priority_phone_number(data)
        return data


class ChangePhoneRequestSerializer(serializers.Serializer):
    new_phone_number = PhoneNumberField()

    def validate_new_phone_number(self, value):
        normalized = value.replace(' ', '').replace('-', '')
        from .utils import validate_priority_phone_number
        validate_priority_phone_number(normalized)

        if User.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError("Bu raqam allaqachon ro'yxatdan o'tgan.")

        return normalized
    

class ConfirmPhoneChangeSerializer(serializers.Serializer):
    auth_code = serializers.CharField()

    def validate(self, data):
        user = self.context['request'].user
        if not user.temp_phone_number:
            raise serializers.ValidationError("Avval telefon raqam o'zgartirishni boshlang.")
        if user.auth_code != data['auth_code']:
            raise serializers.ValidationError("Tasdiqlash kodi noto‘g‘ri.")
        return data


class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField()
    password_confirmation = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'phone_number', 'password', 'password_confirmation',
                    #Shaxsiy malumotlar
                  'first_name', 'last_name', 'role'  
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'password_confirmation': {'write_only': True, 'style': {'input_type': 'password'}},
        }

    def validate_phone_number(self, value):
        normalized = value.replace(' ', '').replace('-', '')  # `normalize_phone` o‘rniga

        # Telefon raqamini priority davlatlar uchun validatsiya qilish
        from .utils import validate_priority_phone_number
        validate_priority_phone_number(normalized)

        # Foydalanuvchi allaqachon ro‘yxatdan o‘tganmi?
        if User.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError("Bu raqam allaqachon ro‘yxatdan o‘tgan.")
        
        return normalized

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')  
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)  
        user.is_active = False  # Ro‘yxatdan o‘tgan foydalanuvchi avval faollashmagan bo‘lishi kerak
        user.save()
        return user


class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    auth_code = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirmation = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirmation']:
            raise serializers.ValidationError({"password": "Parollar mos emas!"})
        return data


class VerifyCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    auth_code = serializers.CharField(max_length=6)


class DriverSerializer(serializers.ModelSerializer):
    carrier = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='carrier'))

    class Meta:
        model = Driver
        fields = '__all__'
        depth = 1
        read_only_fields = ('is_verified',)

 
class Owner_dispatcherSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role__in=['owner', 'dispatcher']))

    class Meta:
        model = OwnerDispatcher
        fields = '__all__'
        read_only_fields = ('is_verified',)
    

class AdminDriverVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['is_verified']
    

class DispatcherOrderSerializer(serializers.ModelSerializer):
    dispatcher = serializers.PrimaryKeyRelatedField(queryset=OwnerDispatcher.objects.filter(user__role='dispatcher', is_verified=True))
    assigned_driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(is_verified=True))
    
    class Meta:
        model = DispatcherOrder
        fields = '__all__'  


class AdminOwnerDispatcherVerificationSerializer(serializers.ModelSerializer):
    """Haydovchining hujjatlarini tastiqlaydi(prava, pasport)"""
    class Meta:
        model = Driver
        fields = ['is_verified']

class DeliverySerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(is_verified=True))
    receiver = serializers.PrimaryKeyRelatedField(queryset=OwnerDispatcher.objects.filter(user__role="owner", is_verified=True))

    class Meta:
        model = DeliveryConfirmation
        fields = '__all__'
        read_only_fields = ['id']


class VehicleSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(is_verified=True))
    
    class Meta:
        model = Vehicle
        fields = '__all__'
    

class BidSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(is_verified=True))

    class Meta:
        model = Bid
        fields = ['driver', 'cargo', 'propose', 'proposed_price']


class BidStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Bid.STATUS_CHOICES)

    class Meta:
        model = Bid
        fields = ["status"]
    

class TrackingSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(is_verified=True))

    class Meta:
        model = Tracking
        fields = ['id', 'cargo', 'driver', 'vehicle', 'current_location', 'status', 'last_updated']
        read_only_fields = ['id']

    
class PaymentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Payment
        fields = '__all__'


class CargoSerializer(serializers.ModelSerializer):
    bids = serializers.SerializerMethodField()  # Barcha bid-larni olish uchun
    customer = serializers.PrimaryKeyRelatedField(queryset=OwnerDispatcher.objects.filter(user__role='owner'))
    
    class Meta:
        model = Cargo
        fields = [
            "id",
            "customer",
            "pickup_region",
            "pickup_location",
            "delivery_region",
            "delivery_location",
            "cargo_type",
            "cargo_status",
            'loading_time', 
            "weight",
            "weight_unit",
            "volume",
            "readiness_choice",
            "readiness",
            "transport_type",
            "placement_method",
            "special_requirements",
            'bids'
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

    def get_bids(self, obj):
        """Har bir Bid uchun 'update-status' URL yaratamiz"""
        request = self.context.get("request")
        bids = obj.bids.all()  # Ushbu yukga tegishli barcha bid-larni olamiz
        return [
            {
                "bid_id": bid.id,
                "propose": bid.propose,
                "status": bid.status,
                "proposed_price": bid.proposed_price,
                "update_url": reverse("bid-update-status", kwargs={"pk": bid.id}, request=request),
            }
            for bid in bids
        ]

    
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class AdministrativeUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdministrativeUnit
        fields = '__all__'
        depth = 1
