# Telegram bot — mahsulot so'rovi

## O'rnatish

```bash
pip install -r requirements.txt
```

## Sozlash (`config.py`)

1. **BOT_TOKEN** — @BotFather orqali olingan token
2. **ANTHROPIC_API_KEY** — Anthropic Console'dan olingan API kalit
3. **GOOGLE_CREDENTIALS_FILE** va **SPREADSHEET_ID** — quyida tushuntirilgan
4. **PHONE_NUMBERS**, **ADMIN_USERNAMES** — tezkor bog'lanish uchun 2 tadan
5. **REGIONS** — kerak bo'lsa ro'yxatni o'zgartirishingiz mumkin

## PostgreSQL ulash

1. PostgreSQL bazasida jadval yarating:
   ```sql
   CREATE TABLE products (
       id SERIAL PRIMARY KEY,
       name TEXT NOT NULL,
       info TEXT
   );
   ```
2. `config.py` dagi `DATABASE_URL` ni o'zingizning bazangizga moslang:
   `postgresql://USER:PASSWORD@HOST:5432/DBNAME`
3. Agar jadval yoki ustun nomlaringiz boshqacha bo'lsa, `config.py` dagi
   `PRODUCTS_TABLE`, `COLUMN_NAME`, `COLUMN_INFO` qiymatlarini o'zgartiring
4. Bot ishga tushganda ulanish pool avtomatik ochiladi (`db.py` → `create_pool`)

## Ishga tushirish

```bash
python bot.py
```

## Oqim tuzilishi

- **/start** → 3 ta tugma: Jismoniy shaxs / Kompaniya / Tezkor bog'lanish
- **Tezkor bog'lanish** → 2 ta telefon raqam + 2 ta admin username ko'rsatiladi
- **Jismoniy shaxs**:
  telefon → mahsulot nomi (AI orqali Sheetdan qidiriladi, topilmasa
  o'xshashlari taklif qilinadi) → ishlatish maqsadi (AI maslahat beradi) →
  yetkazib berish hududi (12 viloyat) → yakun
- **Kompaniya**: kompaniya nomi → mas'ul shaxs → telefon → yakun
  *(bu qism aniq belgilanmagani uchun sodda variant sifatida qo'shildi —
  kerak bo'lsa kengaytirish oson)*

## Eslatma

- `bot.py` ichida `context.user_data` ga yozilgan ma'lumotlarni (telefon,
  mahsulot, maqsad, hudud) CRM/bazaga yoki adminga xabar sifatida
  yuborishni xohlasangiz, `ind_region` va `comp_phone` funksiyalari oxiriga
  qo'shimcha kod qo'shsangiz bo'ladi (masalan admin guruhga xabar yuborish).
