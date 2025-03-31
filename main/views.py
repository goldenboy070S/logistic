from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import BasePermission, IsAdminUser
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions, status
from rest_framework.views import APIView


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
        return UserUpdateSerializer


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


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


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