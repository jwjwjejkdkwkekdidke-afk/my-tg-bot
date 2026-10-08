import os
import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    CopyTextButton,
    ReplyKeyboardRemove
)


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "ВСТАВЬ_СЮДА_ТОКЕН"
)

ADMIN_ID = 8052913358

PAYMENT_CARD = "2204128123651537"

DB_FILE = "auravpn.db"


# =========================================================
# ТАРИФЫ И МНОЖИТЕЛИ УСТРОЙСТВ
# =========================================================

PLANS = {
    7: 39,
    30: 99,
    90: 279,
    180: 549
}

# Коэффициенты цены в зависимости от количества устройств
DEVICE_MULTIPLIERS = {
    1: 1.0,
    3: 2.5,
    5: 4.0
}


# =========================================================
# ЛОГИ
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================================================
# БАЗА ДАННЫХ
# =========================================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            days INTEGER,
            devices INTEGER,
            amount INTEGER,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    conn.close()


def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM banned_users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()
    return result is not None


def ban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def create_purchase(
    user_id: int,
    days: int,
    devices: int,
    amount: int
):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO purchases
        (user_id, days, devices, amount, status)
        VALUES (?, ?, ?, ?, 'pending')
    """, (
        user_id,
        days,
        devices,
        amount
    ))

    purchase_id = cur.lastrowid

    conn.commit()
    conn.close()

    return purchase_id


def update_purchase(
    purchase_id: int,
    status: str
):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE purchases
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            purchase_id
        )
    )

    conn.commit()
    conn.close()


def get_purchase_status(
    purchase_id: int
):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT status
        FROM purchases
        WHERE id = ?
        """,
        (purchase_id,)
    )

    result = cur.fetchone()
    conn.close()

    if result:
        return result[0]

    return None


# =========================================================
# БОТ
# =========================================================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================================================
# НИЖНЯЯ ПАНЕЛЬ
# =========================================================

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🏠 Главное меню"
                ),
                KeyboardButton(
                    text="💳 Купить подписку"
                )
            ],
            [
                KeyboardButton(
                    text="🔐 Мой VPN"
                ),
                KeyboardButton(
                    text="📱 Устройства"
                )
            ],
            [
                KeyboardButton(
                    text="🎁 Пригласить друга"
                ),
                KeyboardButton(
                    text="💬 Поддержка"
                )
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )


# =========================================================
# ГЛАВНОЕ INLINE-МЕНЮ
# =========================================================

def main_menu():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔐 Мой VPN",
        callback_data="menu_vpn"
    )

    builder.button(
        text="💳 Купить подписку",
        callback_data="menu_buy"
    )

    builder.button(
        text="📱 Устройства",
        callback_data="menu_devices"
    )

    builder.button(
        text="🎁 Пригласить друга",
        callback_data="menu_referral"
    )

    builder.button(
        text="💬 Поддержка",
        callback_data="menu_support"
    )

    builder.button(
        text="ℹ️ О сервисе",
        callback_data="menu_about"
    )

    builder.button(
        text="🔽 Скрыть панель",
        callback_data="hide_panel"
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# =========================================================
# ГЛАВНОЕ МЕНЮ — ТЕКСТ
# =========================================================

def welcome_text():
    return (
        "✨ <b>Добро пожаловать в AuraVPN!</b>\n\n"
        "🔐 Быстрый и стабильный VPN\n"
        "🌍 Доступ к нужным сайтам и сервисам\n"
        "⚡ Простое подключение\n\n"
        "<b>Выберите нужный раздел:</b>"
    )


# =========================================================
# КНОПКА НАЗАД
# =========================================================

def back_button():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Главное меню",
        callback_data="main_menu"
    )

    return builder.as_markup()


# =========================================================
# ТАРИФЫ
# =========================================================

def plans_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="7 дней — 39 ₽",
        callback_data="plan_7"
    )

    builder.button(
        text="30 дней — 99 ₽",
        callback_data="plan_30"
    )

    builder.button(
        text="90 дней — 279 ₽",
        callback_data="plan_90"
    )

    builder.button(
        text="180 дней — 549 ₽",
        callback_data="plan_180"
    )

    builder.button(
        text="⬅️ Главное меню",
        callback_data="main_menu"
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()


# =========================================================
# УСТРОЙСТВА (С ДИНАМИЧЕСКИМИ ЦЕНАМИ)
# =========================================================

def devices_keyboard(days: int):
    builder = InlineKeyboardBuilder()
    base_price = PLANS[days]

    for dev_count, multiplier in DEVICE_MULTIPLIERS.items():
        price = int(base_price * multiplier)
        builder.button(
            text=f"📱 {dev_count} устр. — {price} ₽",
            callback_data=f"device_{days}_{dev_count}"
        )

    builder.button(
        text="⬅️ Назад",
        callback_data="menu_buy"
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# ОПЛАТА
# =========================================================

def payment_keyboard(
    days: int,
    devices: int
):
    builder = InlineKeyboardBuilder()

    # КОПИРУЕМАЯ КАРТА
    builder.row(
        InlineKeyboardButton(
            text=f"💳 {PAYMENT_CARD}",
            copy_text=CopyTextButton(
                text=PAYMENT_CARD
            )
        )
    )

    # Я ОПЛАТИЛ
    builder.row(
        InlineKeyboardButton(
            text="✅ Я оплатил",
            callback_data=f"paid_{days}_{devices}"
        )
    )

    # НАЗАД
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"plan_{days}"
        )
    )

    return builder.as_markup()


# =========================================================
# АДМИНСКИЕ КНОПКИ
# =========================================================

def admin_keyboard(
    purchase_id: int,
    user_id: int
):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Принять",
        callback_data=f"accept_{purchase_id}_{user_id}"
    )

    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject_{purchase_id}_{user_id}"
    )

    builder.adjust(2)

    return builder.as_markup()


# =========================================================
# ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ
# =========================================================

async def check_user(
    callback: types.CallbackQuery
):
    if is_banned(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return False

    return True


# =========================================================
# /START
# =========================================================

@dp.message(Command("start"))
async def start_handler(
    message: types.Message
):
    user_id = message.from_user.id

    if is_banned(user_id):
        await message.answer(
            "❌ Вы заблокированы и не можете пользоваться ботом."
        )
        return

    await message.answer(
        welcome_text(),
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================================================
# СКРЫТЬ / ПОКАЗАТЬ ПАНЕЛЬ
# =========================================================

@dp.callback_query(
    F.data == "hide_panel"
)
async def hide_panel_handler(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    await callback.message.answer(
        "🔽 Нижняя панель свернута.",
        reply_markup=ReplyKeyboardRemove()
    )

    builder = InlineKeyboardBuilder()
    builder.button(
        text="📱 Показать панель",
        callback_data="show_panel"
    )
    builder.button(
        text="⬅️ Главное меню",
        callback_data="main_menu"
    )
    builder.adjust(1)

    await callback.message.edit_text(
        "🔽 <b>Панель свернута</b>\n\n"
        "Нижняя клавиатура убрана с экрана. "
        "Вы можете вернуть её в любой момент.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

    await callback.answer("Панель скрыта ✅")


@dp.callback_query(
    F.data == "show_panel"
)
async def show_panel_handler(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    await callback.message.answer(
        "📱 Нижняя панель снова активирована:",
        reply_markup=bottom_keyboard()
    )

    await callback.message.edit_text(
        welcome_text(),
        parse_mode="HTML",
        reply_markup=main_menu()
    )

    await callback.answer("Панель возвращена ✅")


# =========================================================
# НИЖНЯЯ КНОПКА — ГЛАВНОЕ МЕНЮ
# =========================================================

@dp.message(
    F.text == "🏠 Главное меню"
)
async def bottom_main_menu(
    message: types.Message
):
    if is_banned(
        message.from_user.id
    ):
        await message.answer(
            "❌ Вы заблокированы."
        )
        return

    await message.answer(
        "🏠 Главное меню:",
        reply_markup=bottom_keyboard()
    )

    await message.answer(
        welcome_text(),
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================================================
# НИЖНЯЯ КНОПКА — КУПИТЬ
# =========================================================

@dp.message(
    F.text == "💳 Купить подписку"
)
async def bottom_buy(
    message: types.Message
):
    if is_banned(
        message.from_user.id
    ):
        await message.answer(
            "❌ Вы заблокированы."
        )
        return

    await message.answer(
        "💳 <b>Покупка AuraVPN</b>\n\n"
        "Выберите срок подписки:",
        parse_mode="HTML",
        reply_markup=plans_keyboard()
    )


# =========================================================
# НИЖНЯЯ КНОПКА — МОЙ VPN
# =========================================================

@dp.message(
    F.text == "🔐 Мой VPN"
)
