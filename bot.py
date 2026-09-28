import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    GROUP_CHAT_ID,
    REGIONS,
    ADMIN_IDS,
)

from api_client import (
    get_all_products,
    get_product_name,
    format_product_info,
    submit_lead,
    close_api_client,
)

from ai_helper import (
    match_product,
)

import storage


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# STATES
# =========================================================

(
    TYPE_CHOICE,
    IND_PHONE,
    IND_PRODUCT,
    IND_QUANTITY,
    IND_REGION,
    COMP_NAME,
    COMP_PERSON,
    COMP_PHONE,
) = range(8)


(
    ADMIN_MENU,
    ADMIN_ADD_PHONE,
    ADMIN_REMOVE_PHONE,
    ADMIN_ADD_USERNAME,
    ADMIN_REMOVE_USERNAME,
) = range(5)


# =========================================================
# KEYBOARDS
# =========================================================

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["👤 Jismoniy shaxs"],
        ["🏢 Companiya"],
        ["📞 Tezkor bog‘lanish"],
    ],
    resize_keyboard=True,
)


REGION_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Andijon", "Buxoro"],
        ["Farg'ona", "Jizzax"],
        ["Xorazm", "Namangan"],
        ["Navoiy", "Qashqadaryo"],
        ["Samarqand", "Sirdaryo"],
        ["Surxondaryo", "Toshkent viloyati"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


CANCEL_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["❌ Bekor qilish"],
    ],
    resize_keyboard=True,
)


ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📊 Statistika"],
        ["➕ Telefon qo‘shish", "➖ Telefon o‘chirish"],
        ["➕ Username qo‘shish", "➖ Username o‘chirish"],
        ["🔚 Admin panelidan chiqish"],
    ],
    resize_keyboard=True,
)


ADMIN_CANCEL_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["❌ Bekor qilish"],
    ],
    resize_keyboard=True,
)


# =========================================================
# ADMIN HELPERS
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    /start
    """

    context.user_data.clear()

    storage.add_user(
        update.effective_user.id
    )

    await update.message.reply_text(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=MAIN_KEYBOARD,
        parse_mode=ParseMode.HTML,
    )

    return TYPE_CHOICE


# =========================================================
# MENU
# =========================================================

async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Main menu.
    """

    await update.message.reply_text(
        "📋 <b>Asosiy menyu</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=MAIN_KEYBOARD,
        parse_mode=ParseMode.HTML,
    )

    return TYPE_CHOICE


# =========================================================
# CANCEL
# =========================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Cancel current operation.
    """

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Jarayon bekor qilindi.\n\n"
        "Asosiy menyudan foydalanishingiz mumkin.",
        reply_markup=MAIN_KEYBOARD,
    )

    return TYPE_CHOICE


# =========================================================
# QUICK CONTACT
# =========================================================

async def quick_contact(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Quick contact information.
    """

    phone_list = storage.get_phone_numbers()
    username_list = storage.get_admin_usernames()

    phones = "\n".join(
        f"📞 {phone}"
        for phone in phone_list
    )

    admins = "\n".join(
        f"👤 {username}"
        for username in username_list
    )

    text = (
        "📞 <b>Tezkor bog‘lanish</b>\n\n"
        "<b>Telefon raqamlar:</b>\n"
        f"{phones}\n\n"
        "<b>Telegram:</b>\n"
        f"{admins}"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_KEYBOARD,
    )

    return TYPE_CHOICE


# =========================================================
# TYPE CHOICE
# =========================================================

async def type_choice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Choose individual/company/quick contact.
    """

    text = update.message.text.strip()

    if text == "👤 Jismoniy shaxs":

        context.user_data.clear()

        await update.message.reply_text(
            "📱 Telefon raqamingizni kiriting:",
            reply_markup=CANCEL_KEYBOARD,
        )

        return IND_PHONE

    if text == "🏢 Companiya":

        context.user_data.clear()

        await update.message.reply_text(
            "🏢 Kompaniya nomini kiriting:",
            reply_markup=CANCEL_KEYBOARD,
        )

        return COMP_NAME

    if text == "📞 Tezkor bog‘lanish":

        return await quick_contact(
            update,
            context,
        )

    if text == "❌ Bekor qilish":

        return await cancel(
            update,
            context,
        )

    await update.message.reply_text(
        "⚠️ Iltimos, menyudan kerakli bo‘limni tanlang.",
        reply_markup=MAIN_KEYBOARD,
    )

    return TYPE_CHOICE


# =========================================================
# INDIVIDUAL PHONE
# =========================================================

async def individual_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Individual customer phone.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":
        return await cancel(update, context)

    if len(text) < 7:
        await update.message.reply_text(
            "⚠️ Telefon raqamini to‘g‘ri kiriting.\n\n"
            "Masalan:\n"
            "+998901234567",
            reply_markup=CANCEL_KEYBOARD,
        )

        return IND_PHONE

    context.user_data["phone"] = text

    await update.message.reply_text(
        "📦 <b>Qaysi mahsulot kerak?</b>\n\n"
        "Mahsulot nomini yozing:",
        parse_mode=ParseMode.HTML,
        reply_markup=CANCEL_KEYBOARD,
    )

    return IND_PRODUCT


# =========================================================
# INDIVIDUAL PRODUCT
# =========================================================

async def individual_product(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Find product from API.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":
        return await cancel(update, context)

    if not text:
        await update.message.reply_text(
            "⚠️ Mahsulot nomini kiriting.",
            reply_markup=CANCEL_KEYBOARD,
        )

        return IND_PRODUCT

    try:
        logger.info(
            "🔎 Product search: %s",
            text,
        )

        result = await match_product(text)

        logger.info(
            "🔎 Product match result: %r",
            result,
        )

    except Exception as e:

        logger.exception(
            "❌ Mahsulot qidirishda xato: %s",
            e,
        )

        await update.message.reply_text(
            "⚠️ Mahsulotni qidirishda xatolik yuz berdi.\n"
            "Iltimos, qaytadan urinib ko‘ring.",
            reply_markup=CANCEL_KEYBOARD,
        )

        return IND_PRODUCT

    # -----------------------------------------------------
    # RESULT NORMALIZATION
    # -----------------------------------------------------

    product_name = None
    product = None

    if isinstance(result, dict):

        product_name = (
            result.get("product_name")
            or result.get("name")
            or result.get("title")
        )

        product = result.get("product")

    elif isinstance(result, str):

        product_name = result

    # -----------------------------------------------------
    # NO PRODUCT
    # -----------------------------------------------------

    if not product_name and not product:

        await update.message.reply_text(
            "❌ <b>Mahsulot topilmadi.</b>\n\n"
            "Mahsulot nomini aniqroq yozib ko‘ring.",
            parse_mode=ParseMode.HTML,
            reply_markup=CANCEL_KEYBOARD,
        )

        return IND_PRODUCT

    # -----------------------------------------------------
    # PRODUCT OBJECT
    # -----------------------------------------------------

    if isinstance(product, dict):

        actual_product_name = (
            get_product_name(product)
            or product_name
            or text
        )

        context.user_data["product"] = actual_product_name
        context.user_data["product_data"] = product

        try:
            product_info = format_product_info(product)
        except Exception:

            product_info = (
                f"📦 <b>{actual_product_name}</b>"
            )

    else:

        actual_product_name = (
            product_name
            or text
        )

        context.user_data["product"] = actual_product_name

        # Try API search again to get complete product information
        product_info = None

        try:

            products = await get_all_products()

            for item in products:

                name = get_product_name(item)

                if (
                    name
                    and name.lower()
                    == actual_product_name.lower()
                ):
                    context.user_data["product_data"] = item

                    product_info = format_product_info(
                        item
                    )

                    break

        except Exception as e:

            logger.exception(
                "❌ Product details error: %s",
                e,
            )

        if not product_info:

            product_info = (
                f"📦 <b>{actual_product_name}</b>"
            )

    # -----------------------------------------------------
    # SHOW PRODUCT
    # -----------------------------------------------------

    await update.message.reply_text(
        product_info,
        parse_mode=ParseMode.HTML,
        reply_markup=CANCEL_KEYBOARD,
    )

    await update.message.reply_text(
        "🔢 <b>Nechta olmoqchisiz?</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=CANCEL_KEYBOARD,
    )

    return IND_QUANTITY


# =========================================================
# INDIVIDUAL QUANTITY
# =========================================================

async def individual_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Quantity.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":
        return await cancel(update, context)

    # Keep only digits
    if not text.isdigit():

        await update.message.reply_text(
            "⚠️ Miqdorni faqat raqam bilan kiriting.\n\n"
            "Masalan: 5",
            reply_markup=CANCEL_KEYBOARD,
        )

        return IND_QUANTITY

    quantity = int(text)

    if quantity <= 0:

        await update.message.reply_text(
            "⚠️ Miqdor 0 dan katta bo‘lishi kerak.",
            reply_markup=CANCEL_KEYBOARD,
        )

        return IND_QUANTITY

    context.user_data["quantity"] = quantity

    await update.message.reply_text(
        "📍 <b>Qaysi viloyatdansiz?</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=REGION_KEYBOARD,
    )

    return IND_REGION


# =========================================================
# SEND INDIVIDUAL LEAD TO GROUP
# =========================================================

async def send_individual_lead_to_group(
    context: ContextTypes.DEFAULT_TYPE,
    lead_data: dict,
):
    """
    Send individual lead directly to Telegram group.
    """

    group_text = (
        "🆕 <b>YANGI MIJOZ</b>\n\n"
        "👤 <b>Jismoniy shaxs</b>\n\n"
        f"📱 Telefon: "
        f"<code>{lead_data['phone']}</code>\n"
        f"📦 Mahsulot: "
        f"{lead_data['product']}\n"
        f"🔢 Miqdor: "
        f"{lead_data['quantity']}\n"
        f"📍 Viloyat: "
        f"{lead_data['region']}"
    )

    try:

        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=group_text,
            parse_mode=ParseMode.HTML,
        )

        logger.info(
            "✅ Individual lead Telegram guruhga yuborildi."
        )

        return True

    except Exception as e:

        logger.exception(
            "❌ Individual lead guruhga yuborishda xato: %s",
            e,
        )

        return False


# =========================================================
# INDIVIDUAL REGION
# =========================================================

async def individual_region(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Region and final lead submission.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":
        return await cancel(update, context)

    # Check region
    if text not in REGIONS:

        await update.message.reply_text(
            "⚠️ Iltimos, viloyatni ro‘yxatdan tanlang.",
            reply_markup=REGION_KEYBOARD,
        )

        return IND_REGION

    context.user_data["region"] = text

    lead_data = {
        "type": "individual",
        "phone": context.user_data.get(
            "phone",
            "",
        ),
        "product": context.user_data.get(
            "product",
            "",
        ),
        "quantity": context.user_data.get(
            "quantity",
            0,
        ),
        "region": context.user_data.get(
            "region",
            "",
        ),
    }

    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "========================================"
    )

    logger.info(
        "📤 SENDING INDIVIDUAL LEAD"
    )

    logger.info(
        "Phone: %s",
        lead_data["phone"],
    )

    logger.info(
        "Product: %s",
        lead_data["product"],
    )

    logger.info(
        "Quantity: %s",
        lead_data["quantity"],
    )

    logger.info(
        "Region: %s",
        lead_data["region"],
    )

    logger.info(
        "========================================"
    )

    # =====================================================
    # 1. API GA YUBORISH
    # =====================================================

    api_success = False

    try:

        result = await submit_lead(
            lead_data
        )

        logger.info(
            "📥 submit_lead result: %r",
            result,
        )

        if result is not None:
            api_success = True
            logger.info(
                "✅ Lead API ga yuborildi."
            )
        else:
            logger.error(
                "❌ submit_lead() None qaytardi."
            )

    except Exception as e:

        logger.exception(
            "❌ Lead API ga yuborishda xato: %s",
            e,
        )

    # =====================================================
    # 2. TELEGRAM GROUP GA YUBORISH
    # =====================================================

    group_success = await send_individual_lead_to_group(
        context,
        lead_data,
    )

    # =====================================================
    # USERGA JAVOB
    # =====================================================

    if group_success:

        await update.message.reply_text(
            "✅ <b>Ma'lumotlaringiz qabul qilindi!</b>\n\n"
            "📦 Mahsulot: "
            f"{lead_data['product']}\n"
            "🔢 Miqdor: "
            f"{lead_data['quantity']}\n"
            "📍 Viloyat: "
            f"{lead_data['region']}\n\n"
            "📞 Tez orada siz bilan bog‘lanamiz.",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_KEYBOARD,
        )

    else:

        await update.message.reply_text(
            "⚠️ Ma'lumotlarni saqlashda muammo yuz berdi.\n\n"
            "Iltimos, birozdan keyin qayta urinib ko‘ring.",
            reply_markup=MAIN_KEYBOARD,
        )

    context.user_data.clear()

    return TYPE_CHOICE


# =========================================================
# COMPANY NAME
# =========================================================

async def company_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Company name.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":
        return await cancel(update, context)

    if not text:

        await update.message.reply_text(
            "⚠️ Kompaniya nomini kiriting.",
            reply_markup=CANCEL_KEYBOARD,
        )

        return COMP_NAME

    context.user_data["company_name"] = text

    await update.message.reply_text(
        "👤 Mas'ul xodimning ismini kiriting:",
        reply_markup=CANCEL_KEYBOARD,
    )

    return COMP_PERSON


# =========================================================
# COMPANY PERSON
# =========================================================

async def company_person(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Responsible person.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":
        return await cancel(update, context)

    if not text:

        await update.message.reply_text(
            "⚠️ Mas'ul xodim ismini kiriting.",
            reply_markup=CANCEL_KEYBOARD,
        )

        return COMP_PERSON

    context.user_data["contact_person"] = text

    await update.message.reply_text(
        "📱 Telefon raqamini kiriting:",
        reply_markup=CANCEL_KEYBOARD,
    )

    return COMP_PHONE


# =========================================================
# SEND COMPANY LEAD TO GROUP
# =========================================================

async def send_company_lead_to_group(
    context: ContextTypes.DEFAULT_TYPE,
    lead_data: dict,
):
    """
    Send company lead directly to Telegram group.
    """

    group_text = (
        "🆕 <b>YANGI MIJOZ</b>\n\n"
        "🏢 <b>Kompaniya</b>\n\n"
        f"🏢 Kompaniya: "
        f"{lead_data['company_name']}\n"
        f"👤 Mas'ul: "
        f"{lead_data['contact_person']}\n"
        f"📱 Telefon: "
        f"<code>{lead_data['phone']}</code>"
    )

    try:

        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=group_text,
            parse_mode=ParseMode.HTML,
        )

        logger.info(
            "✅ Company lead Telegram guruhga yuborildi."
        )

        return True

    except Exception as e:

        logger.exception(
            "❌ Company lead guruhga yuborishda xato: %s",
            e,
        )

        return False


# =========================================================
# COMPANY PHONE
# =========================================================

async def company_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Company phone and final submission.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":
        return await cancel(update, context)

    if len(text) < 7:

        await update.message.reply_text(
            "⚠️ Telefon raqamini to‘g‘ri kiriting.",
            reply_markup=CANCEL_KEYBOARD,
        )

        return COMP_PHONE

    context.user_data["phone"] = text

    lead_data = {
        "type": "company",
        "company_name": context.user_data.get(
            "company_name",
            "",
        ),
        "contact_person": context.user_data.get(
            "contact_person",
            "",
        ),
        "phone": context.user_data.get(
            "phone",
            "",
        ),
    }

    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "========================================"
    )

    logger.info(
        "📤 SENDING COMPANY LEAD"
    )

    logger.info(
        "Company: %s",
        lead_data["company_name"],
    )

    logger.info(
        "Person: %s",
        lead_data["contact_person"],
    )

    logger.info(
        "Phone: %s",
        lead_data["phone"],
    )

    logger.info(
        "========================================"
    )

    # =====================================================
    # 1. API
    # =====================================================

    api_success = False

    try:

        result = await submit_lead(
            lead_data
        )

        logger.info(
            "📥 submit_lead result: %r",
            result,
        )

        if result is not None:

            api_success = True

            logger.info(
                "✅ Company lead API ga yuborildi."
            )

        else:

            logger.error(
                "❌ Company submit_lead() None qaytardi."
            )

    except Exception as e:

        logger.exception(
            "❌ Company Lead API error: %s",
            e,
        )

    # =====================================================
    # 2. TELEGRAM GROUP
    # =====================================================

    group_success = await send_company_lead_to_group(
        context,
        lead_data,
    )

    # =====================================================
    # USER RESPONSE
    # =====================================================

    if group_success:

        await update.message.reply_text(
            "✅ <b>Ma'lumotlaringiz qabul qilindi!</b>\n\n"
            "🏢 Kompaniya: "
            f"{lead_data['company_name']}\n"
            "👤 Mas'ul: "
            f"{lead_data['contact_person']}\n"
            "📱 Telefon: "
            f"{lead_data['phone']}\n\n"
            "📞 Tez orada siz bilan bog‘lanamiz.",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_KEYBOARD,
        )

    else:

        await update.message.reply_text(
            "⚠️ Ma'lumotlarni yuborishda muammo yuz berdi.\n"
            "Iltimos, qaytadan urinib ko‘ring.",
            reply_markup=MAIN_KEYBOARD,
        )

    context.user_data.clear()

    return TYPE_CHOICE


# =========================================================
# PRODUCTS COMMAND
# =========================================================

async def products_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    /products
    """

    try:

        products = await get_all_products()

    except Exception as e:

        logger.exception(
            "❌ Products API error: %s",
            e,
        )

        await update.message.reply_text(
            "❌ Mahsulotlarni olishda xatolik yuz berdi."
        )

        return TYPE_CHOICE

    if not products:

        await update.message.reply_text(
            "📦 Hozircha mahsulotlar mavjud emas."
        )

        return TYPE_CHOICE

    text_lines = [
        "📦 <b>Mahsulotlar</b>",
        "",
    ]

    for index, product in enumerate(
        products[:50],
        start=1,
    ):

        name = get_product_name(product)

        if name:
            text_lines.append(
                f"{index}. {name}"
            )

    text = "\n".join(text_lines)

    # Telegram message max size protection
    if len(text) > 4000:

        text = text[:3950] + "\n..."

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_KEYBOARD,
    )

    return TYPE_CHOICE


# =========================================================
# ADMIN: ENTRY (/admin)
# =========================================================

async def admin_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    /admin — faqat ADMIN_IDS ro'yxatidagi userlar uchun.
    """

    user_id = update.effective_user.id

    if not is_admin(user_id):

        await update.message.reply_text(
            "⛔ Sizda bu buyruqdan foydalanish huquqi yo‘q."
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "🛠 <b>Admin panel</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        parse_mode=ParseMode.HTML,
        reply_markup=ADMIN_KEYBOARD,
    )

    return ADMIN_MENU


# =========================================================
# ADMIN: MENU
# =========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Admin panel asosiy menyusi.
    """

    text = update.message.text.strip()

    if text == "📊 Statistika":

        user_count = storage.get_user_count()

        await update.message.reply_text(
            "📊 <b>Statistika</b>\n\n"
            f"👥 Botga /start bosgan userlar soni: "
            f"<b>{user_count}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=ADMIN_KEYBOARD,
        )

        return ADMIN_MENU

    if text == "➕ Telefon qo‘shish":

        await update.message.reply_text(
            "📱 Qo‘shmoqchi bo‘lgan telefon raqamni kiriting:\n\n"
            "Masalan:\n"
            "+998901234567",
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_ADD_PHONE

    if text == "➖ Telefon o‘chirish":

        phone_list = storage.get_phone_numbers()

        if not phone_list:

            await update.message.reply_text(
                "📭 Hozircha telefon raqamlar mavjud emas.",
                reply_markup=ADMIN_KEYBOARD,
            )

            return ADMIN_MENU

        phones_text = "\n".join(
            f"{index}. {phone}"
            for index, phone in enumerate(
                phone_list,
                start=1,
            )
        )

        await update.message.reply_text(
            "➖ <b>O‘chirmoqchi bo‘lgan raqamni yozing:</b>\n\n"
            f"{phones_text}",
            parse_mode=ParseMode.HTML,
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_REMOVE_PHONE

    if text == "➕ Username qo‘shish":

        await update.message.reply_text(
            "👤 Qo‘shmoqchi bo‘lgan Telegram usernameni kiriting:\n\n"
            "Masalan:\n"
            "@username",
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_ADD_USERNAME

    if text == "➖ Username o‘chirish":

        username_list = storage.get_admin_usernames()

        if not username_list:

            await update.message.reply_text(
                "📭 Hozircha usernamelar mavjud emas.",
                reply_markup=ADMIN_KEYBOARD,
            )

            return ADMIN_MENU

        usernames_text = "\n".join(
            f"{index}. {username}"
            for index, username in enumerate(
                username_list,
                start=1,
            )
        )

        await update.message.reply_text(
            "➖ <b>O‘chirmoqchi bo‘lgan usernameni yozing:</b>\n\n"
            f"{usernames_text}",
            parse_mode=ParseMode.HTML,
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_REMOVE_USERNAME

    if text == "🔚 Admin panelidan chiqish":

        await update.message.reply_text(
            "🔚 Admin paneldan chiqdingiz.",
            reply_markup=MAIN_KEYBOARD,
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "⚠️ Iltimos, menyudan kerakli bo‘limni tanlang.",
        reply_markup=ADMIN_KEYBOARD,
    )

    return ADMIN_MENU


# =========================================================
# ADMIN: ADD PHONE
# =========================================================

async def admin_add_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Yangi telefon raqamni saqlaydi.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":

        await update.message.reply_text(
            "❌ Bekor qilindi.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ADMIN_MENU

    if len(text) < 7:

        await update.message.reply_text(
            "⚠️ Telefon raqamini to‘g‘ri kiriting.\n\n"
            "Masalan:\n"
            "+998901234567",
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_ADD_PHONE

    added = storage.add_phone_number(text)

    if added:

        await update.message.reply_text(
            f"✅ <b>{text}</b> raqami qo‘shildi.",
            parse_mode=ParseMode.HTML,
            reply_markup=ADMIN_KEYBOARD,
        )

    else:

        await update.message.reply_text(
            "⚠️ Bu raqam allaqachon ro‘yxatda mavjud.",
            reply_markup=ADMIN_KEYBOARD,
        )

    return ADMIN_MENU


# =========================================================
# ADMIN: REMOVE PHONE
# =========================================================

async def admin_remove_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Mavjud telefon raqamni o'chiradi.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":

        await update.message.reply_text(
            "❌ Bekor qilindi.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ADMIN_MENU

    removed = storage.remove_phone_number(text)

    if removed:

        await update.message.reply_text(
            f"✅ <b>{text}</b> raqami o‘chirildi.",
            parse_mode=ParseMode.HTML,
            reply_markup=ADMIN_KEYBOARD,
        )

    else:

        await update.message.reply_text(
            "⚠️ Bunday raqam ro‘yxatda topilmadi.\n\n"
            "Raqamni ro‘yxatdagidek aniq yozing.",
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_REMOVE_PHONE

    return ADMIN_MENU


# =========================================================
# ADMIN: ADD USERNAME
# =========================================================

async def admin_add_username(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Yangi admin usernameni saqlaydi.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":

        await update.message.reply_text(
            "❌ Bekor qilindi.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ADMIN_MENU

    if len(text) < 3:

        await update.message.reply_text(
            "⚠️ Usernameni to‘g‘ri kiriting.\n\n"
            "Masalan:\n"
            "@username",
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_ADD_USERNAME

    if not text.startswith("@"):
        text = f"@{text}"

    added = storage.add_admin_username(text)

    if added:

        await update.message.reply_text(
            f"✅ <b>{text}</b> username qo‘shildi.",
            parse_mode=ParseMode.HTML,
            reply_markup=ADMIN_KEYBOARD,
        )

    else:

        await update.message.reply_text(
            "⚠️ Bu username allaqachon ro‘yxatda mavjud.",
            reply_markup=ADMIN_KEYBOARD,
        )

    return ADMIN_MENU


# =========================================================
# ADMIN: REMOVE USERNAME
# =========================================================

async def admin_remove_username(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Mavjud admin usernameni o'chiradi.
    """

    text = update.message.text.strip()

    if text == "❌ Bekor qilish":

        await update.message.reply_text(
            "❌ Bekor qilindi.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ADMIN_MENU

    if not text.startswith("@"):
        text = f"@{text}"

    removed = storage.remove_admin_username(text)

    if removed:

        await update.message.reply_text(
            f"✅ <b>{text}</b> username o‘chirildi.",
            parse_mode=ParseMode.HTML,
            reply_markup=ADMIN_KEYBOARD,
        )

    else:

        await update.message.reply_text(
            "⚠️ Bunday username ro‘yxatda topilmadi.\n\n"
            "Usernameni ro‘yxatdagidek aniq yozing.",
            reply_markup=ADMIN_CANCEL_KEYBOARD,
        )

        return ADMIN_REMOVE_USERNAME

    return ADMIN_MENU


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Global error handler.
    """

    logger.exception(
        "❌ Bot error: %s",
        context.error,
    )

    try:

        if isinstance(update, Update):

            if update.effective_message:

                await update.effective_message.reply_text(
                    "⚠️ Kutilmagan xatolik yuz berdi.\n"
                    "Iltimos, qaytadan urinib ko‘ring.",
                    reply_markup=MAIN_KEYBOARD,
                )

    except Exception as e:

        logger.exception(
            "❌ Error message yuborishda xato: %s",
            e,
        )


# =========================================================
# POST INIT
# =========================================================

async def post_init(
    application: Application,
):
    """
    Bot startup.
    """

    logger.info(
        "========================================"
    )

    logger.info(
        "🚀 BOT IS STARTING..."
    )

    logger.info(
        "GROUP_CHAT_ID: %s",
        GROUP_CHAT_ID,
    )

    logger.info(
        "ADMIN_IDS: %s",
        ADMIN_IDS,
    )

    logger.info(
        "========================================"
    )

    # Load products at startup
    try:

        products = await get_all_products()

        logger.info(
            "✅ %s ta mahsulot yuklandi.",
            len(products),
        )

    except Exception as e:

        logger.exception(
            "❌ Mahsulotlarni yuklashda xato: %s",
            e,
        )


# =========================================================
# POST SHUTDOWN
# =========================================================

async def post_shutdown(
    application: Application,
):
    """
    Shutdown.
    """

    try:

        await close_api_client()

    except Exception as e:

        logger.exception(
            "❌ API client yopishda xato: %s",
            e,
        )

    logger.info(
        "🛑 Bot stopped."
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN config.py da mavjud emas!"
        )

    if not GROUP_CHAT_ID:

        raise ValueError(
            "GROUP_CHAT_ID config.py da mavjud emas!"
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # =====================================================
    # ADMIN CONVERSATION
    # =====================================================
    # MUHIM: bu handler asosiy (mijozlar) conversationdan OLDIN
    # ro'yxatdan o'tkaziladi. Aks holda, agar admin avval /start
    # bosgan bo'lsa (asosiy conversationda "ochiq holat" qolib
    # ketadi), uning admin-panel tugmalari asosiy conversation
    # tomonidan "tutib qolinib", "Iltimos, menyudan tanlang"
    # xabari chiqaveradi.

    admin_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "admin",
                admin_start,
            ),
        ],

        states={

            ADMIN_MENU: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_menu,
                ),
            ],

            ADMIN_ADD_PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_add_phone,
                ),
            ],

            ADMIN_REMOVE_PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_remove_phone,
                ),
            ],

            ADMIN_ADD_USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_add_username,
                ),
            ],

            ADMIN_REMOVE_USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_remove_username,
                ),
            ],
        },

        fallbacks=[
            CommandHandler(
                "admin",
                admin_start,
            ),
        ],

        allow_reentry=True,
    )

    application.add_handler(
        admin_conversation_handler
    )

    # =====================================================
    # MAIN CONVERSATION
    # =====================================================

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "start",
                start,
            ),
        ],

        states={

            TYPE_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    type_choice,
                ),
            ],

            IND_PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    individual_phone,
                ),
            ],

            IND_PRODUCT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    individual_product,
                ),
            ],

            IND_QUANTITY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    individual_quantity,
                ),
            ],

            IND_REGION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    individual_region,
                ),
            ],

            COMP_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    company_name,
                ),
            ],

            COMP_PERSON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    company_person,
                ),
            ],

            COMP_PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    company_phone,
                ),
            ],
        },

        fallbacks=[
            CommandHandler(
                "start",
                start,
            ),
            MessageHandler(
                filters.Regex("^❌ Bekor qilish$"),
                cancel,
            ),
        ],

        allow_reentry=True,
    )

    application.add_handler(
        conversation_handler
    )

    # /products
    application.add_handler(
        CommandHandler(
            "products",
            products_command,
        )
    )

    # /menu
    application.add_handler(
        CommandHandler(
            "menu",
            menu,
        )
    )

    # Error handler
    application.add_error_handler(
        error_handler
    )

    logger.info(
        "🤖 Bot polling started..."
    )

    application.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()