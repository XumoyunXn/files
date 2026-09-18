import asyncio
import logging
import re
import unicodedata
from difflib import SequenceMatcher

from google import genai

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

from api_client import (
    get_all_products,
    get_product_name,
    get_product_description,
    get_product_price,
    format_product_info,
)

logger = logging.getLogger(__name__)


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# CYRILLIC -> LATIN
# =========================================================

CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "j",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sh",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "қ": "q",
    "ғ": "g",
    "ҳ": "h",
    "ў": "o",
}


# =========================================================
# NORMALIZE
# =========================================================

def normalize_text(text):
    """
    Oddiy normalizatsiya.
    """

    if not text:
        return ""

    text = str(text)

    text = text.lower().strip()

    # Unicode normalizatsiya
    text = unicodedata.normalize(
        "NFKC",
        text
    )

    # Har xil tirelarni bitta ko'rinishga o'tkazamiz
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = text.replace("−", "-")
    text = text.replace("_", "-")

    # Apostroflar
    text = text.replace("'", "")
    text = text.replace('"', "")
    text = text.replace("`", "")

    # Ortiqcha space
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# TRANSLITERATION
# =========================================================

def transliterate(text):
    """
    Kirill va lotin yozuvlarini bir xil ko'rinishga
    keltirish uchun ishlatiladi.

    Masalan:

    Реле -> rele
    Rele -> rele

    Сириус -> sirius
    Sirius -> sirius
    """

    text = normalize_text(text)

    result = []

    for char in text:

        if char in CYRILLIC_TO_LATIN:
            result.append(
                CYRILLIC_TO_LATIN[char]
            )
        else:
            result.append(char)

    return "".join(result)


# =========================================================
# SEARCH NORMALIZE
# =========================================================

def search_normalize(text):
    """
    Mahsulot qidirish uchun kuchli normalizatsiya.

    Masalan:

    Сириус-2-Л-К — Реле тока
    Sirius 2 Л К Rele toka

    o'xshash shaklga keladi.
    """

    text = transliterate(text)

    # Faqat harf va raqamlarni qoldiramiz
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# COMPACT NORMALIZE
# =========================================================

def compact_normalize(text):
    """
    Bo'sh joy va belgilarni ham olib tashlaydi.

    Sirius-2-L-K
    Sirius 2 L K

    -> sirius2lk
    """

    text = search_normalize(text)

    return text.replace(
        " ",
        ""
    )


# =========================================================
# WORDS
# =========================================================

def get_words(text):

    text = search_normalize(
        text
    )

    return set(
        word
        for word in text.split()
        if len(word) >= 2
    )


# =========================================================
# TOKEN SCORE
# =========================================================

def token_score(
    user_text,
    product_name
):

    user_words = get_words(
        user_text
    )

    product_words = get_words(
        product_name
    )

    if not user_words or not product_words:
        return 0

    common = (
        user_words
        & product_words
    )

    if not common:
        return 0

    # Foydalanuvchi yozgan so'zlarning qanchasi
    # mahsulot nomida bor
    user_coverage = (
        len(common)
        / len(user_words)
    ) * 100

    # Mahsulot nomidagi so'zlarning qanchasi
    # topilgan
    product_coverage = (
        len(common)
        / len(product_words)
    ) * 100

    # O'rtacha
    score = (
        user_coverage
        + product_coverage
    ) / 2

    return int(score)


# =========================================================
# SIMILARITY SCORE
# =========================================================

def similarity_score(
    user_text,
    product_name
):

    if not user_text or not product_name:
        return 0

    user = search_normalize(
        user_text
    )

    product = search_normalize(
        product_name
    )

    if not user or not product:
        return 0

    # =====================================================
    # 1. EXACT
    # =====================================================

    if user == product:
        return 100

    # =====================================================
    # 2. COMPACT EXACT
    # =====================================================

    user_compact = compact_normalize(
        user_text
    )

    product_compact = compact_normalize(
        product_name
    )

    if user_compact == product_compact:
        return 99

    # =====================================================
    # 3. CONTAINS
    # =====================================================

    if user in product:
        return 95

    if product in user:
        return 93

    # =====================================================
    # 4. COMPACT CONTAINS
    # =====================================================

    if (
        user_compact
        and product_compact
    ):

        if user_compact in product_compact:
            return 92

        if product_compact in user_compact:
            return 90

    # =====================================================
    # 5. TOKEN SCORE
    # =====================================================

    token = token_score(
        user_text,
        product_name
    )

    # =====================================================
    # 6. FUZZY SCORE
    # =====================================================

    fuzzy = int(
        SequenceMatcher(
            None,
            user,
            product
        ).ratio() * 100
    )

    # =====================================================
    # 7. COMBINED SCORE
    # =====================================================

    score = max(
        token,
        fuzzy
    )

    # Agar token va fuzzy ikkalasi ham yaxshi bo'lsa
    if token >= 50 and fuzzy >= 50:

        score = max(
            score,
            int(
                (token + fuzzy) / 2
            )
        )

    return int(score)


# =========================================================
# LOCAL PRODUCT SEARCH
# =========================================================

async def simple_title_search(
    product_name
):

    if not product_name:
        return None

    products = await get_all_products()

    if not products:
        logger.warning(
            "API mahsulotlari mavjud emas."
        )

        return None

    user_normalized = search_normalize(
        product_name
    )

    user_compact = compact_normalize(
        product_name
    )

    # =====================================================
    # 1. EXACT NORMALIZED MATCH
    # =====================================================

    for product in products:

        name = get_product_name(
            product
        )

        if not name:
            continue

        normalized_name = search_normalize(
            name
        )

        if normalized_name == user_normalized:

            logger.info(
                "✅ Exact product found: %s",
                name
            )

            return product

    # =====================================================
    # 2. COMPACT MATCH
    # =====================================================

    for product in products:

        name = get_product_name(
            product
        )

        if not name:
            continue

        normalized_name = compact_normalize(
            name
        )

        if (
            normalized_name
            == user_compact
        ):

            logger.info(
                "✅ Compact product found: %s",
                name
            )

            return product

    # =====================================================
    # 3. CONTAINS MATCH
    # =====================================================

    for product in products:

        name = get_product_name(
            product
        )

        if not name:
            continue

        normalized_name = search_normalize(
            name
        )

        if (
            user_normalized in normalized_name
            or normalized_name in user_normalized
        ):

            logger.info(
                "✅ Contains product found: %s",
                name
            )

            return product

    # =====================================================
    # 4. SCORE BASED SEARCH
    # =====================================================

    best_product = None
    best_score = 0

    for product in products:

        name = get_product_name(
            product
        )

        if not name:
            continue

        score = similarity_score(
            product_name,
            name
        )

        logger.debug(
            "Product score | %s | %s",
            name,
            score
        )

        if score > best_score:

            best_score = score
            best_product = product

    # =====================================================
    # 5. GOOD MATCH
    # =====================================================

    if best_product and best_score >= 60:

        name = get_product_name(
            best_product
        )

        logger.info(
            "✅ Product found by similarity: %s | score=%s",
            name,
            best_score
        )

        return best_product

    logger.info(
        "❌ Local product search failed: %s | best_score=%s",
        product_name,
        best_score
    )

    return None


# =========================================================
# ALTERNATIVES
# =========================================================

async def simple_alternatives(
    product_name,
    limit=3
):

    products = await get_all_products()

    if not products:
        return []

    scored = []

    for product in products:

        name = get_product_name(
            product
        )

        if not name:
            continue

        score = similarity_score(
            product_name,
            name
        )

        if score > 0:

            scored.append(
                (
                    score,
                    product
                )
            )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    result = []

    seen = set()

    for score, product in scored:

        name = get_product_name(
            product
        )

        normalized = search_normalize(
            name
        )

        if normalized in seen:
            continue

        seen.add(normalized)

        result.append(
            product
        )

        if len(result) >= limit:
            break

    return result


# =========================================================
# GEMINI REQUEST
# =========================================================

async def _generate_content(
    prompt
):

    try:

        logger.info(
            "Gemini request boshlandi..."
        )

        task = asyncio.to_thread(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
        )

        try:

            response = await asyncio.wait_for(
                task,
                timeout=15
            )

        except asyncio.TimeoutError:

            logger.warning(
                "⚠️ Gemini timeout: 15 sekund"
            )

            return ""

        if not response:
            return ""

        text = (
            response.text
            or ""
        ).strip()

        logger.info(
            "Gemini response olindi."
        )

        return text

    except Exception as e:

        logger.warning(
            "Gemini error: %s",
            e
        )

        return ""


# =========================================================
# ASK AI
# =========================================================

async def ask_ai(
    prompt
):

    result = await _generate_content(
        prompt
    )

    if result:
        return result

    logger.warning(
        "Gemini birinchi urinishda javob bermadi."
    )

    await asyncio.sleep(
        1
    )

    result = await _generate_content(
        prompt
    )

    if result:
        return result

    logger.error(
        "❌ Gemini ishlamadi."
    )

    return ""


# =========================================================
# MATCH PRODUCT
# =========================================================

async def match_product(
    user_text
):

    user_text = (
        user_text
        or ""
    ).strip()

    if not user_text:

        return {
            "found": False,
            "product": None,
            "product_name": "",
            "alternatives": [],
            "source": "empty",
        }

    logger.info(
        "🔎 Product search: %s",
        user_text
    )

    # =====================================================
    # 1. LOCAL API SEARCH
    # =====================================================

    product = await simple_title_search(
        user_text
    )

    if product:

        name = get_product_name(
            product
        )

        logger.info(
            "✅ API product found: %s",
            name
        )

        return {
            "found": True,
            "product": product,
            "product_name": name,
            "alternatives": [],
            "source": "api_local",
        }

    # =====================================================
    # 2. GET API PRODUCTS
    # =====================================================

    products = await get_all_products()

    if not products:

        return {
            "found": False,
            "product": None,
            "product_name": "",
            "alternatives": [],
            "source": "api_empty",
        }

    # =====================================================
    # 3. PREPARE PRODUCT NAMES
    # =====================================================

    product_list = []

    for product in products:

        name = get_product_name(
            product
        )

        if name:
            product_list.append(
                name
            )

    if not product_list:

        return {
            "found": False,
            "product": None,
            "product_name": "",
            "alternatives": [],
            "source": "no_names",
        }

    # =====================================================
    # 4. GEMINI
    # =====================================================

    prompt = f"""
Siz mahsulot qidiruvchi yordamchisiz.

Foydalanuvchi yozgan mahsulot:

"{user_text}"

API bazasidagi mahsulotlar:

{chr(10).join(product_list)}

Vazifa:

1. Foydalanuvchi yozgan mahsulotni API
   mahsulotlari bilan solishtiring.

2. Lotin va kirill yozuvlari farqini
   hisobga oling.

Masalan:
Rele = Реле

3. Agar mos mahsulot mavjud bo'lsa,
   API bazasidagi mahsulot nomini aynan
   o'sha ko'rinishda qaytaring.

4. Agar mos mahsulot bo'lmasa:

NOT_FOUND

Faqat mahsulot nomi yoki NOT_FOUND yozing.
"""

    ai_result = await ask_ai(
        prompt
    )

    ai_result = (
        ai_result
        or ""
    ).strip()

    # =====================================================
    # 5. CLEAN AI RESPONSE
    # =====================================================

    ai_result = (
        ai_result
        .replace("```", "")
        .replace("**", "")
        .strip()
    )

    # Gemini ba'zida izoh bilan javob berishi mumkin
    if (
        ai_result
        and ai_result != "NOT_FOUND"
        and len(ai_result) < 200
    ):

        # =================================================
        # EXACT AI PRODUCT
        # =================================================

        for product in products:

            name = get_product_name(
                product
            )

            if not name:
                continue

            if (
                search_normalize(name)
                == search_normalize(ai_result)
            ):

                logger.info(
                    "✅ Gemini product found: %s",
                    name
                )

                return {
                    "found": True,
                    "product": product,
                    "product_name": name,
                    "alternatives": [],
                    "source": "gemini",
                }

        # =================================================
        # FUZZY AI PRODUCT
        # =================================================

        best_product = None
        best_score = 0

        for product in products:

            name = get_product_name(
                product
            )

            score = similarity_score(
                ai_result,
                name
            )

            if score > best_score:

                best_score = score
                best_product = product

        if (
            best_product
            and best_score >= 75
        ):

            name = get_product_name(
                best_product
            )

            logger.info(
                "✅ Gemini fuzzy product found: %s | score=%s",
                name,
                best_score
            )

            return {
                "found": True,
                "product": best_product,
                "product_name": name,
                "alternatives": [],
                "source": "gemini_fuzzy",
            }

    # =====================================================
    # 6. FALLBACK ALTERNATIVES
    # =====================================================

    alternatives = await simple_alternatives(
        user_text,
        limit=3
    )

    logger.info(
        "🔁 Alternatives found: %s",
        len(alternatives)
    )

    return {
        "found": False,
        "product": None,
        "product_name": "",
        "alternatives": alternatives,
        "source": "fallback",
    }


# =========================================================
# PRODUCT DESCRIPTION
# =========================================================

async def get_product_description_by_name(
    product_name
):

    product = await simple_title_search(
        product_name
    )

    if not product:
        return ""

    return get_product_description(
        product
    )


# =========================================================
# PRODUCT PRICE
# =========================================================

async def get_product_price_by_name(
    product_name
):

    product = await simple_title_search(
        product_name
    )

    if not product:
        return None

    return get_product_price(
        product
    )


# =========================================================
# USAGE ADVICE
# =========================================================

async def usage_advice(
    product_name,
    purpose
):

    product = await simple_title_search(
        product_name
    )

    if not product:

        return (
            "Mahsulot haqida ma'lumot topilmadi."
        )

    description = get_product_description(
        product
    )

    prompt = f"""
Mahsulot:
{product_name}

API tavsifi:
{description}

Mijoz mahsulotni quyidagi maqsadda
ishlatmoqchi:

{purpose}

API ma'lumotlariga asoslanib,
mijozga qisqa va tushunarli maslahat bering.

Mahsulotda mavjud bo'lmagan xususiyatni
o'ylab topmang.

Agar API tavsifida kerakli ma'lumot
bo'lmasa, buni ochiq ayting.
"""

    result = await ask_ai(
        prompt
    )

    if result:
        return result

    return (
        "Mahsulot API ma'lumotlariga ko‘ra "
        "ushbu foydalanish uchun mos kelishi mumkin."
    )


# =========================================================
# SUGGEST ALTERNATIVES
# =========================================================

async def suggest_alternatives(
    product_name,
    limit=3
):

    return await simple_alternatives(
        product_name,
        limit
    )


# =========================================================
# FORMAT PRODUCT
# =========================================================

async def get_product_info(
    product_name
):

    product = await simple_title_search(
        product_name
    )

    if not product:
        return None

    return format_product_info(
        product
    )