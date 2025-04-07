import random

def generate_auth_code():
    """Tasodifiy 6 xonali tasdiqlash kodini yaratish"""
    return "".join(random.choices("0123456789", k=6))