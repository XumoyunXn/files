import libsql_client

from config import TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, PRODUCTS_TABLE, COLUMN_NAME, COLUMN_INFO


async def create_pool() -> libsql_client.Client:
    """
    Turso (libsql) uchun PostgreSQL'dagidek alohida connection pool kerak emas —
    bitta client kifoya. Funksiya nomi bot.py bilan mos kelishi uchun saqlab qolindi.
    """
    return libsql_client.create_client(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN,
    )


async def get_all_products(client: libsql_client.Client) -> list[dict]:
    """
    products jadvalidan barcha mahsulotlarni o'qiydi.
    Jadval tuzilishi (namuna, SQLite/libsql sintaksisi):
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            info TEXT
        );
    """
    query = f"SELECT {COLUMN_NAME}, {COLUMN_INFO} FROM {PRODUCTS_TABLE}"
    result_set = await client.execute(query)
    return [dict(zip(result_set.columns, row)) for row in result_set.rows]


def get_product_names(products: list[dict]) -> list[str]:
    return [str(p.get(COLUMN_NAME, "")).strip() for p in products if p.get(COLUMN_NAME)]


def find_product_info(products: list[dict], name: str) -> str:
    name_lower = name.strip().lower()
    for p in products:
        if str(p.get(COLUMN_NAME, "")).strip().lower() == name_lower:
            return p.get(COLUMN_INFO) or "Ma'lumot topilmadi."
    return "Ma'lumot topilmadi."