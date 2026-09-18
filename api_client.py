import logging
import httpx

from config import (
    API_PRODUCTS_URL,
    API_LEADS_URL,
    API_TIMEOUT,
)

logger = logging.getLogger(__name__)

_products_cache = None


# =========================================================
# API'DAN BARCHA MAHSULOTLARNI OLISH
# =========================================================

async def get_all_products(force_refresh=False):

    global _products_cache

    # Cache bor bo'lsa qayta API chaqirilmaydi
    if _products_cache is not None and not force_refresh:
        return _products_cache

    try:

        async with httpx.AsyncClient(
            timeout=API_TIMEOUT
        ) as client:

            response = await client.get(
                API_PRODUCTS_URL
            )

            logger.info(
                "Products API status: %s",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()

        # =================================================
        # API RESPONSE
        # =================================================

        products = []

        if isinstance(data, list):

            products = data

        elif isinstance(data, dict):

            # {
            #   "data": [...]
            # }

            if isinstance(
                data.get("data"),
                list
            ):

                products = data["data"]

            # {
            #   "products": [...]
            # }

            elif isinstance(
                data.get("products"),
                list
            ):

                products = data["products"]

            # {
            #   "results": [...]
            # }

            elif isinstance(
                data.get("results"),
                list
            ):

                products = data["results"]

        # =================================================
        # NORMALIZE
        # =================================================

        normalized = []

        for product in products:

            if not isinstance(
                product,
                dict
            ):
                continue

            # Strapi format
            #
            # {
            #   "id": 1,
            #   "attributes": {
            #       ...
            #   }
            # }

            if isinstance(
                product.get("attributes"),
                dict
            ):

                attributes = product[
                    "attributes"
                ]

                product = {
                    "id": product.get("id"),
                    **attributes,
                }

            normalized.append(
                product
            )

        _products_cache = normalized

        logger.info(
            "✅ %s ta mahsulot yuklandi.",
            len(_products_cache)
        )

        return _products_cache

    except Exception as e:

        logger.exception(
            "❌ Products API xatosi: %s",
            e
        )

        return []


# =========================================================
# MAHSULOT NOMINI OLISH
# =========================================================

def get_product_name(product):

    if not isinstance(
        product,
        dict
    ):
        return ""

    return str(
        product.get("title")
        or product.get("name")
        or product.get("product_name")
        or product.get("TITLE")
        or product.get("productTitle")
        or ""
    ).strip()


# =========================================================
# NARXNI OLISH
# =========================================================

def get_product_price(product):

    if not isinstance(
        product,
        dict
    ):
        return None

    return (
        product.get("price")
        or product.get("PRICE")
        or product.get("Price")
        or product.get("selling_price")
    )


# =========================================================
# ESKI NARX
# =========================================================

def get_old_price(product):

    if not isinstance(
        product,
        dict
    ):
        return None

    return (
        product.get("old_price")
        or product.get("OLD_PRICE")
        or product.get("oldPrice")
    )


# =========================================================
# TAVSIF
# =========================================================

def get_product_description(product):

    if not isinstance(
        product,
        dict
    ):
        return ""

    return str(
        product.get("description")
        or product.get("full_description")
        or product.get("short_description")
        or product.get("FULL_DESCRIPTION")
        or product.get("SHORT_DESCRIPTION")
        or ""
    ).strip()


# =========================================================
# QISQA TAVSIF
# =========================================================

def get_short_description(product):

    if not isinstance(
        product,
        dict
    ):
        return ""

    return str(
        product.get("short_description")
        or product.get("SHORT_DESCRIPTION")
        or product.get("description")
        or ""
    ).strip()


# =========================================================
# KATEGORIYA
# =========================================================

def get_product_category(product):

    if not isinstance(
        product,
        dict
    ):
        return ""

    category = (
        product.get("category")
        or product.get("category_name")
        or product.get("CATEGORY")
        or product.get("CATEGORY_NAME")
    )

    if isinstance(
        category,
        dict
    ):

        return str(
            category.get("name")
            or category.get("title")
            or ""
        ).strip()

    return str(
        category or ""
    ).strip()


# =========================================================
# SKU
# =========================================================

def get_product_sku(product):

    if not isinstance(
        product,
        dict
    ):
        return ""

    return str(
        product.get("sku")
        or product.get("SKU")
        or ""
    ).strip()


# =========================================================
# STOCK
# =========================================================

def get_stock_count(product):

    if not isinstance(
        product,
        dict
    ):
        return None

    return (
        product.get("stock_count")
        or product.get("stockCount")
        or product.get("STOCK_COUNT")
    )


# =========================================================
# IN STOCK
# =========================================================

def get_in_stock(product):

    if not isinstance(
        product,
        dict
    ):
        return None

    value = (
        product.get("in_stock")
        if "in_stock" in product
        else product.get("inStock")
    )

    if value is None:
        value = product.get("IN_STOCK")

    return value


# =========================================================
# RATING
# =========================================================

def get_rating(product):

    if not isinstance(
        product,
        dict
    ):
        return None

    return (
        product.get("rating")
        or product.get("RATING")
    )


# =========================================================
# REVIEW COUNT
# =========================================================

def get_review_count(product):

    if not isinstance(
        product,
        dict
    ):
        return None

    return (
        product.get("review_count")
        or product.get("reviewCount")
        or product.get("REVIEW_COUNT")
    )


# =========================================================
# IMAGE
# =========================================================

def get_product_image(product):

    if not isinstance(
        product,
        dict
    ):
        return ""

    image = (
        product.get("image")
        or product.get("image_url")
        or product.get("imageUrl")
        or product.get("IMAGE")
        or product.get("IMAGE_URL")
    )

    if isinstance(
        image,
        dict
    ):

        return str(
            image.get("url")
            or image.get("src")
            or ""
        )

    return str(
        image or ""
    )


# =========================================================
# TEXT NORMALIZE
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    return (
        str(text)
        .lower()
        .strip()
        .replace("'", "")
        .replace('"', "")
    )


# =========================================================
# PRODUCT SEARCH
# =========================================================

async def search_products(
    search_text
):

    products = await get_all_products()

    query = normalize_text(
        search_text
    )

    if not query:
        return []

    results = []

    for product in products:

        name = normalize_text(
            get_product_name(product)
        )

        sku = normalize_text(
            get_product_sku(product)
        )

        category = normalize_text(
            get_product_category(product)
        )

        description = normalize_text(
            get_product_description(product)
        )

        searchable = " ".join([
            name,
            sku,
            category,
            description,
        ])

        if query in searchable:

            results.append(product)

    return results


# =========================================================
# EXACT PRODUCT
# =========================================================

async def find_product_info(
    product_name
):

    products = await get_all_products()

    query = normalize_text(
        product_name
    )

    # 1. Exact
    for product in products:

        name = normalize_text(
            get_product_name(product)
        )

        if name == query:

            return product

    # 2. Contains
    for product in products:

        name = normalize_text(
            get_product_name(product)
        )

        if (
            query in name
            or name in query
        ):

            return product

    return None


# =========================================================
# PRODUCT NAMES
# =========================================================

async def get_product_names():

    products = await get_all_products()

    names = []

    for product in products:

        name = get_product_name(
            product
        )

        if name:
            names.append(name)

    return names


# =========================================================
# FORMAT PRODUCT
# =========================================================

def format_product_info(
    product
):

    if not product:

        return "❌ Mahsulot topilmadi."

    name = get_product_name(
        product
    )

    price = get_product_price(
        product
    )

    old_price = get_old_price(
        product
    )

    description = get_product_description(
        product
    )

    category = get_product_category(
        product
    )

    sku = get_product_sku(
        product
    )

    stock = get_stock_count(
        product
    )

    in_stock = get_in_stock(
        product
    )

    rating = get_rating(
        product
    )

    review_count = get_review_count(
        product
    )

    text = ""

    text += f"📦 <b>{name}</b>\n\n"

    if category:

        text += (
            f"🏷 Kategoriya: "
            f"{category}\n"
        )

    if sku:

        text += (
            f"🔖 SKU: "
            f"{sku}\n"
        )

    if price is not None:

        text += (
            f"💰 Narx: "
            f"{price} so'm\n"
        )

    if old_price is not None:

        text += (
            f"💵 Eski narx: "
            f"{old_price} so'm\n"
        )

    if in_stock is not None:

        if in_stock:

            text += "✅ Mavjud\n"

        else:

            text += "❌ Mavjud emas\n"

    if stock is not None:

        text += (
            f"📊 Qoldiq: "
            f"{stock} dona\n"
        )

    if rating is not None:

        text += (
            f"⭐ Reyting: "
            f"{rating}\n"
        )

    if review_count is not None:

        text += (
            f"💬 Sharhlar: "
            f"{review_count}\n"
        )

    if description:

        text += (
            "\n📝 <b>Tavsif:</b>\n"
            f"{description}\n"
        )

    return text


# =========================================================
# SEND LEAD
# =========================================================

async def submit_lead(
    lead_data
):

    try:

        async with httpx.AsyncClient(
            timeout=API_TIMEOUT
        ) as client:

            response = await client.post(
                API_LEADS_URL,
                json=lead_data
            )

            logger.info(
                "Lead API status: %s",
                response.status_code
            )

            if response.status_code >= 400:

                logger.error(
                    "Lead API error: %s",
                    response.text
                )

                return None

            try:

                return response.json()

            except Exception:

                return {
                    "success": True
                }

    except Exception as e:

        logger.exception(
            "❌ Lead API xatosi: %s",
            e
        )

        return None


# =========================================================
# CACHE CLEAR
# =========================================================

def clear_products_cache():

    global _products_cache

    _products_cache = None

    logger.info(
        "Product cache tozalandi."
    )


# =========================================================
# CLOSE
# =========================================================

async def close_api_client():

    pass