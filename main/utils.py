import random
import phonenumbers

from phonenumbers import parse, is_valid_number, NumberParseException
from django.core.exceptions import ValidationError
from phonenumbers import NumberParseException
def generate_auth_code():
    """Tasodifiy 6 xonali tasdiqlash kodini yaratish"""
    return "".join(random.choices("0123456789", k=6))


PRIORITY_COUNTRIES_CODES = {
    '+998': {'valid_codes': ['90', '91', '93', '94', '95', '97', '98', '99', '33', '88'], 'length': 7},
    '+7': {'valid_codes': ['700', '701', '702', '705', '707', '747', '771', '775', '776', '777', '912', '913', '914', '915', '916', '917', '918', '919', '920' ], 'length': 7},
    '+1': {'valid_codes': ['201', '202', '203', '204', '205', '206', '207', '208', '209','212', '213', '214', '215', '216', '217', '218', '219', '224','225', '226', '228', '229', '231', '234', '239', '240', '248','250', '251', '252', '253', '254', '256', '260', '262', '267'], 'length': 7},
    '+82': {'valid_codes': ['10', '11', '16', '17'], 'length': 8},
    '+90': {'valid_codes': ['501', '505', '506', '507', '530', '531', '532', '533', '534', '535', '536', '537', '538', '539'], 'length': 7},
    '+996': {'valid_codes': ['500', '501', '502', '504', '505', '507', '508', '509'], 'length': 7},
    '+992': {'valid_codes': ['917', '918', '919', '915', '988', '987'], 'length': 7},
    '+993': {'valid_codes': ['61', '62', '63', '64', '65'], 'length': 7},
    '+994': {'valid_codes': ['50', '51', '55', '70', '77'], 'length': 7},
    '+966': {'valid_codes': ['50', '53', '54', '55', '56', '57', '58', '59'], 'length': 7},
}

def validate_priority_phone_number(phone: str):
    phone = phone.replace(' ', '').replace('-', '')

    for prefix, info in PRIORITY_COUNTRIES_CODES.items():
        if phone.startswith(prefix):
            without_prefix = phone[len(prefix):]

            # Har xil uzunlikdagi operator kodlari (2 yoki 3 belgili)
            possible_codes = sorted(info['valid_codes'], key=len, reverse=True)  # eng uzun kodni avval tekshiramiz
            for code in possible_codes:
                if without_prefix.startswith(code):
                    number_part = without_prefix[len(code):]
                    if len(number_part) != info['length']:
                        raise ValidationError(f"{prefix} raqam uzunligi noto‘g‘ri: {code} dan keyin {info['length']} ta raqam bo‘lishi kerak.")
                    return True

            raise ValidationError(f"{prefix} uchun operator kodi noto‘g‘ri.")
    raise ValidationError("Telefon raqam ruxsat berilmagan davlat kodi bilan boshlanmoqda.")