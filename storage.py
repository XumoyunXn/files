import json
import logging
from pathlib import Path

from config import PHONE_NUMBERS, ADMIN_USERNAMES


logger = logging.getLogger(__name__)


# =========================================================
# PATHS
# =========================================================

DATA_DIR = Path("data")

USERS_FILE = DATA_DIR / "users.json"
PHONES_FILE = DATA_DIR / "phones.json"
USERNAMES_FILE = DATA_DIR / "usernames.json"


# =========================================================
# LOW LEVEL HELPERS
# =========================================================

def _ensure_data_dir():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def _load_json(
    path: Path,
    default,
):
    _ensure_data_dir()

    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        logger.exception(
            "❌ JSON o'qishda xato (%s): %s",
            path,
            e,
        )

        return default


def _save_json(
    path: Path,
    data,
):
    _ensure_data_dir()

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

    except Exception as e:
        logger.exception(
            "❌ JSON yozishda xato (%s): %s",
            path,
            e,
        )


# =========================================================
# USERS (bot foydalanuvchilari)
# =========================================================

def add_user(user_id: int) -> bool:
    """
    /start bosgan userni ro'yxatga qo'shadi.
    Yangi user bo'lsa True, avval ham bo'lgan bo'lsa False qaytaradi.
    """

    users = _load_json(
        USERS_FILE,
        [],
    )

    if user_id in users:
        return False

    users.append(user_id)

    _save_json(
        USERS_FILE,
        users,
    )

    return True


def get_user_count() -> int:
    users = _load_json(
        USERS_FILE,
        [],
    )

    return len(users)


# =========================================================
# PHONE NUMBERS (admin qo'sha oladigan raqamlar)
# =========================================================

def get_phone_numbers() -> list:
    """
    Fayl mavjud bo'lmasa, config.py dagi standart raqamlar bilan
    boshlanadi.
    """

    if not PHONES_FILE.exists():

        default_phones = [
            phone
            for phone in PHONE_NUMBERS
            if phone
        ]

        _save_json(
            PHONES_FILE,
            default_phones,
        )

        return default_phones

    return _load_json(
        PHONES_FILE,
        [],
    )


def add_phone_number(phone: str) -> bool:
    """
    Yangi telefon raqam qo'shadi.
    Allaqachon mavjud bo'lsa False qaytaradi.
    """

    phones = get_phone_numbers()

    if phone in phones:
        return False

    phones.append(phone)

    _save_json(
        PHONES_FILE,
        phones,
    )

    return True


def remove_phone_number(phone: str) -> bool:
    """
    Telefon raqamni ro'yxatdan o'chiradi.
    """

    phones = get_phone_numbers()

    if phone not in phones:
        return False

    phones.remove(phone)

    _save_json(
        PHONES_FILE,
        phones,
    )

    return True


# =========================================================
# ADMIN USERNAMES (admin qo'sha oladigan Telegram usernamelar)
# =========================================================

def get_admin_usernames() -> list:
    """
    Fayl mavjud bo'lmasa, config.py dagi standart usernamelar bilan
    boshlanadi.
    """

    if not USERNAMES_FILE.exists():

        default_usernames = [
            username
            for username in ADMIN_USERNAMES
            if username
        ]

        _save_json(
            USERNAMES_FILE,
            default_usernames,
        )

        return default_usernames

    return _load_json(
        USERNAMES_FILE,
        [],
    )


def add_admin_username(username: str) -> bool:
    """
    Yangi admin username qo'shadi.
    Allaqachon mavjud bo'lsa False qaytaradi.
    """

    usernames = get_admin_usernames()

    if username in usernames:
        return False

    usernames.append(username)

    _save_json(
        USERNAMES_FILE,
        usernames,
    )

    return True


def remove_admin_username(username: str) -> bool:
    """
    Admin usernameni ro'yxatdan o'chiradi.
    """

    usernames = get_admin_usernames()

    if username not in usernames:
        return False

    usernames.remove(username)

    _save_json(
        USERNAMES_FILE,
        usernames,
    )

    return True