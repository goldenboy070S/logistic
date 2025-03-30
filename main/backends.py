from django.contrib.auth.backends import ModelBackend
from main.models import User  # User modelini import qilish

class PhoneNumberAuthBackend(ModelBackend):
    """
    Telefon raqam orqali autentifikatsiya backend.
    """
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        try:
            user = User.objects.get(phone_number=phone_number)
            if user.check_password(password):  # Parolni tekshiramiz
                return user
        except User.DoesNotExist:
            return None
        return None
