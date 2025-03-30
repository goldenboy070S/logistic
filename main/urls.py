from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('orders', OrderViewSet)
router.register('drivers', DriverViewSet)
router.register('vehicles', VehicleViewSet)
router.register('trackings', TrackingViewSet)
router.register('payments', PaymentViewSet)
router.register('cargos',CargoViewSet)
router.register('regions', RegionViewSet, basename='regions')
router.register('deliveries', DeliveryConfirmationViewSet)


urlpatterns = router.urls