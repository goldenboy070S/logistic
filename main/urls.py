from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *
router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('drivers', DriverViewSet)
router.register('owner-dispatcher', OwnerDispatcherViewSet)
router.register('vehicles', VehicleViewSet)
router.register('cargos',CargoViewSet)
router.register('bids', BidViewSet, basename='bids')
router.register('trackings', TrackingViewSet)
router.register('payments', PaymentViewSet)
router.register('dispatcherOrder', DispatcherViewSet)
router.register('deliveries', DeliveryConfirmationViewSet)
router.register('regions', RegionViewSet, basename='regions')
router.register('administreviteUnits', AdministraviteUnitViewSet)

urlpatterns = [
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),  
    path('', include(router.urls)),
    path("bids/<int:pk>/update-status/", BidViewSet.as_view({'patch': 'update_status'}), name="bid-update-status")
]