import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

API_PRODUCTS_URL = os.getenv("API_PRODUCTS_URL")
API_LEADS_URL = os.getenv("API_LEADS_URL")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))

PHONE_NUMBERS = [
    os.getenv("PHONE_NUMBER_1"),
    os.getenv("PHONE_NUMBER_2"),
    os.getenv("PHONE_NUMBER_3"),
]

ADMIN_USERNAMES = [
    os.getenv("ADMIN_USERNAME_1"),
    os.getenv("ADMIN_USERNAME_2"),
]

# Admin foydalanuvchilar (statistika ko'rish, telefon qo'shish huquqiga ega)
# .env fayliga ADMIN_IDS=34687360,123456 tarzida qo'shsangiz, shu yerda
# avtomatik o'qiladi. Hech narsa qo'shilmasa, standart qiymat ishlatiladi.
ADMIN_IDS = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "34687360").split(",")
    if admin_id.strip()
]

REGIONS = [
    "Andijon",
    "Buxoro",
    "Farg'ona",
    "Jizzax",
    "Xorazm",
    "Namangan",
    "Navoiy",
    "Qashqadaryo",
    "Samarqand",
    "Sirdaryo",
    "Surxondaryo",
    "Toshkent viloyati",
]