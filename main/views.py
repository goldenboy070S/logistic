from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions, status
from rest_framework.views import APIView
from .utils import generate_auth_code

class IsAuthenticatedOrPostOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST' and not request.user.is_authenticated or request.user.is_superuser:
            return True
        elif request.method == 'GET' and request.user.is_superuser:
            return True
        return False    


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrPostOnly]  
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'verify_code':
            return VerifyCodeSerializer
        elif self.action in ['resend_verification_code', 'last_code']:
            return serializers.Serializer  # oddiy serializer talab qilinmasa
        return UserUpdateSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def resend_verification_code(self, request):
        phone_number = request.data.get("phone_number")
        try:
            user = User.objects.get(phone_number=phone_number, is_active=False)
        except User.DoesNotExist:
            return Response(
                {"error": "Foydalanuvchi topilmadi yoki allaqachon tasdiqlangan!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Auth code yangilash
        user.auth_code = generate_auth_code()  # Utilsdan import qilingan funksiya
        user.save()


        print(f"TEST MODE: {phone_number} uchun tasdiqlash kodi: {user.auth_code}")

        return Response({
            "message": "Tasdiqlash kodi qayta yuborildi!",
            "test_auth_code": user.auth_code  # faqat test rejimi uchun
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[])
    def verify_code(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data[request.user.phone_number]
        auth_code = serializer.validated_data["auth_code"]
        try:
            user = User.objects.get(phone_number=phone_number, auth_code=auth_code, is_active=False)
        except User.DoesNotExist:
            return Response(
                {"error": "Tasdiqlash kodi noto‘g‘ri yoki allaqachon faollashtirilgan!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.auth_code = None
        user.save()

        return Response({"message": "Foydalanuvchi muvaffaqiyatli faollashtirildi!"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[])
    def test(self, request):   
        """Test rejimi: telefon raqam bo‘yicha auth_code ni ko‘rsatish"""
        phone_number = request.data.get("phone_number")

        if not phone_number:
            return Response({"error": "Telefon raqam yuboring!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error": "Foydalanuvchi topilmadi!"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "phone_number": phone_number,
            "auth_code": user.auth_code  # Endi bu yerda foydalanuvchining auth_code qiymati ko'rsatiladi
        }, status=status.HTTP_200_OK)


class RegionViewSet(ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    @action(detail=True, methods=["get"])
    def units(self, request, pk=None):
        """Viloyatga bog‘langan shahar/tumanlarni qaytaradi"""
        region = self.get_object()
        units = AdministrativeUnit.objects.filter(region=region)
        serializer = AdministrativeUnitSerializer(units, many=True)
        return Response(serializer.data)


class DriverViewSet(ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def verify(self, request, pk=None):
        """Haydovchini tasdiqlash (faqat adminlar uchun)"""
        driver = get_object_or_404(Driver, pk=pk)
        if driver.is_verified:
            return Response({"message": "Bu haydovchi allaqachon tasdiqlangan!"}, status=400)
        serializer = AdminDriverVerificationSerializer(driver, data={'is_verified': True}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Haydovchi tasdiqlandi!"})
        return Response(serializer.errors, status=400)


class OwnerDispatcherViewSet(ModelViewSet):
    queryset = OwnerDispatcher.objects.all()
    serializer_class = Owner_dispatcherSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def verify(self, request, pk=None):
        """owner va dispatcherlarni tasdiqlash (faqat adminlar uchun)"""
        user = get_object_or_404(OwnerDispatcher, pk=pk)
        if user.is_verified:
             return Response({"message": "Bu foydalanuvchi allaqachon tasdiqlangan!"}, status=400)
        serializer = AdminOwnerDispatcherVerificationSerializer(user, data={'is_verified': True}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "foydalanuvchi tasdiqlandi!"})
        return Response(serializer.errors, status=400)


class VehicleViewSet(ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class TrackingViewSet(ModelViewSet):
    queryset = Tracking.objects.all()
    serializer_class = TrackingSerializer


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class CargoViewSet(ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer


class DeliveryConfirmationViewSet(ModelViewSet):
    queryset = DeliveryConfirmation.objects.all()
    serializer_class = DeliverySerializer


class DispatcherViewSet(ModelViewSet):
    queryset = DispatcherOrder.objects.all()
    serializer_class = DispatcherOrderSerializer


class BidViewSet(ModelViewSet):
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            owner_dispatcher = OwnerDispatcher.objects.filter(user=self.request.user).first()
            if owner_dispatcher:
                return Bid.objects.filter(
                    cargo__customer=owner_dispatcher,
                    cargo__bids__status__in=['pending', 'rejected']  # accepted bo‘lmaganlar
                ).distinct()
        return Bid.objects.none()

    def update_status(self, request, pk=None):
        bid = get_object_or_404(Bid, id=pk)

        # Faqat yuk egasi bid statusini o'zgartira oladi
        owner_dispatcher = OwnerDispatcher.objects.filter(user=request.user).first()
        if not owner_dispatcher or bid.cargo.customer != owner_dispatcher:
            return Response(
                {"error": "Siz faqat o'zingizning yuklaringizga berilgan bid-larni boshqara olasiz!"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BidStatusUpdateSerializer(bid, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Bid statusi yangilandi!", "bid": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        cargo = serializer.validated_data['cargo']
        
        # Agar bu yukga allaqachon accepted holatidagi bid bo‘lsa
        if Bid.objects.filter(cargo=cargo, status='accepted').exists():
            raise ValidationError({"detail": "Bu yukga allaqachon biror taklif tasdiqlangan. Yangi taklif yuborish mumkin emas."})
        
        serializer.save()



class AdministraviteUnitViewSet(ModelViewSet):
    queryset = AdministrativeUnit.objects.all()
    serializer_class = AdministrativeUnitSerializer 