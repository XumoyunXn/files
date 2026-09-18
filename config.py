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
]

ADMIN_USERNAMES = [
    os.getenv("ADMIN_USERNAME_1"),
    os.getenv("ADMIN_USERNAME_2"),
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