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
# ЛОГИРОВАНИЕ
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
# ИНИЦИАЛИЗАЦИЯ БОТА И ДИСПЕТЧЕРА
# =========================================================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================================================
# НИЖНЯЯ ПАНЕЛЬ КЛАВИАТУРЫ
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
# ТЕКСТ ПРИВЕТСТВИЯ
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
# КНОПКА ВОЗВРАТА НАЗАД
# =========================================================

def back_button():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Главное меню",
        callback_data="main_menu"
    )

    return builder.as_markup()


# =========================================================
# МЕНЮ ТАРИФОВ
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
# ВЫБОР УСТРОЙСТВ
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
# КЛАВИАТУРА ОПЛАТЫ
# =========================================================

def payment_keyboard(
    days: int,
    devices: int
):
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Я оплатил",
            callback_data=f"paid_{days}_{devices}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"plan_{days}"
        )
    )

    return builder.as_markup()


# =========================================================
# АДМИНСКАЯ КЛАВИАТУРА ЗАЯВОК
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
# ПРОВЕРКА СТАТУСА БЛОКИРОВКИ ПОЛЬЗОВАТЕЛЯ
# =========================================================

async def check_user(
    callback: types.CallbackQuery
) -> bool:
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
# КОМАНДА /START
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
# УПРАВЛЕНИЕ НИЖНЕЙ ПАНЕЛЬЮ (СКРЫТЬ / ПОКАЗАТЬ)
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

    text = (
        "🔽 <b>Панель свернута</b>\n\n"
        "Нижняя клавиатура убрана с экрана. "
        "Вы можете вернуть её в любой момент."
    )
    await callback.message.edit_text(
        text,
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
# ОБРАБОТЧИКИ НИЖНИХ КНОПОК
# =========================================================

@dp.message(
    F.text == "🏠 Главное меню"
)
async def bottom_main_menu(
    message: types.Message
):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
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


@dp.message(
    F.text == "💳 Купить подписку"
)
async def bottom_buy(
    message: types.Message
):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return

    await message.answer(
        "💳 <b>Покупка AuraVPN</b>\n\n"
        "Выберите срок подписки:",
        parse_mode="HTML",
        reply_markup=plans_keyboard()
    )


@dp.message(
    F.text == "🔐 Мой VPN"
)
async def bottom_vpn(
    message: types.Message
):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return

    await message.answer(
        "🔐 <b>Мой VPN</b>\n\n"
        "Активная подписка не найдена.\n\n"
        "Чтобы получить VPN, приобретите подписку.",
        parse_mode="HTML",
        reply_markup=back_button()
    )


@dp.message(
    F.text == "📱 Устройства"
)
async def bottom_devices(
    message: types.Message
):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return

    await message.answer(
        "📱 <b>Устройства</b>\n\n"
        "Количество устройств выбирается при покупке подписки.",
        parse_mode="HTML",
        reply_markup=back_button()
    )


@dp.message(
    F.text == "🎁 Пригласить друга"
)
async def bottom_referral(
    message: types.Message
):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return

    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"

    await message.answer(
        "🎁 <b>Пригласить друга</b>\n\n"
        "Ваша реферальная ссылка:\n\n"
        f"<code>{link}</code>",
        parse_mode="HTML",
        reply_markup=back_button()
    )


@dp.message(
    F.text == "💬 Поддержка"
)
async def bottom_support(
    message: types.Message
):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return

    await message.answer(
        "💬 <b>Поддержка</b>\n\n"
        "Если у вас возникли проблемы с оплатой или подключением, "
        "напишите администратору.",
        parse_mode="HTML",
        reply_markup=back_button()
    )


# =========================================================
# ОБРАБОТЧИКИ INLINE-КНОПОК МЕНЮ
# =========================================================

@dp.callback_query(
    F.data == "main_menu"
)
async def main_menu_callback(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    await callback.message.edit_text(
        welcome_text(),
        parse_mode="HTML",
        reply_markup=main_menu()
    )

    await callback.answer()


@dp.callback_query(
    F.data == "menu_vpn"
)
async def menu_vpn(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    text = (
        "🔐 <b>Мой VPN</b>\n\n"
        "Активная подписка не найдена.\n\n"
        "Приобретите подписку, чтобы получить доступ."
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button()
    )

    await callback.answer()


@dp.callback_query(
    F.data == "menu_buy"
)
async def menu_buy(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    text = (
        "💳 <b>Покупка AuraVPN</b>\n\n"
        "Выберите срок подписки:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=plans_keyboard()
    )

    await callback.answer()


@dp.callback_query(
    F.data == "menu_devices"
)
async def menu_devices(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    text = (
        "📱 <b>Устройства</b>\n\n"
        "Количество устройств выбирается при покупке подписки."
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button()
    )

    await callback.answer()


@dp.callback_query(
    F.data == "menu_referral"
)
async def menu_referral(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{callback.from_user.id}"

    text = (
        "🎁 <b>Пригласить друга</b>\n\n"
        "Ваша реферальная ссылка:\n\n"
        f"<code>{link}</code>"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button()
    )

    await callback.answer()


@dp.callback_query(
    F.data == "menu_support"
)
async def menu_support(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    text = (
        "💬 <b>Поддержка</b>\n\n"
        "Если у вас возникли проблемы с оплатой или подключением, "
        "напишите администратору."
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button()
    )

    await callback.answer()


@dp.callback_query(
    F.data == "menu_about"
)
async def menu_about(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    text = (
        "ℹ️ <b>О AuraVPN</b>\n\n"
        "🔐 Защита соединения\n"
        "⚡ Быстрое подключение\n"
        "🌍 Доступ к нужным ресурсам\n"
        "📱 Поддержка нескольких устройств"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button()
    )

    await callback.answer()


# =========================================================
# ВЫБОР ТАРИФОВ ПО ДНЯМ
# =========================================================

@dp.callback_query(
    F.data == "plan_7"
)
async def plan_7(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return
    await show_devices(callback, 7)


@dp.callback_query(
    F.data == "plan_30"
)
async def plan_30(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return
    await show_devices(callback, 30)


@dp.callback_query(
    F.data == "plan_90"
)
async def plan_90(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return
    await show_devices(callback, 90)


@dp.callback_query(
    F.data == "plan_180"
)
async def plan_180(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return
    await show_devices(callback, 180)


async def show_devices(
    callback: types.CallbackQuery,
    days: int
):
    price = PLANS[days]

    text = (
        f"💳 <b>Подписка на {days} дней</b>\n\n"
        f"💰 Базовая стоимость (1 устр.): <b>{price} ₽</b>\n\n"
        "📱 Выберите количество устройств:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=devices_keyboard(days)
    )

    await callback.answer()


# =========================================================
# ВЫБОР УСТРОЙСТВА И ПЕРЕХОД К ОПЛАТЕ
# =========================================================

@dp.callback_query(
    F.data.startswith("device_")
)
async def device_handler(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    try:
        parts = callback.data.split("_")
        days = int(parts[1])
        devices = int(parts[2])
    except (
        ValueError,
        IndexError
    ):
        await callback.answer(
            "Ошибка выбора тарифа.",
            show_alert=True
        )
        return

    if days not in PLANS or devices not in DEVICE_MULTIPLIERS:
        await callback.answer(
            "Неизвестный тариф.",
            show_alert=True
        )
        return

    multiplier = DEVICE_MULTIPLIERS[devices]
    price = int(PLANS[days] * multiplier)

    text = (
        "💳 <b>Оплата AuraVPN</b>\n\n"
        f"📅 Срок: <b>{days} дней</b>\n"
        f"📱 Устройств: <b>{devices}</b>\n"
        f"💰 Сумма к оплате: <b>{price} ₽</b>\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "💳 <b>Реквизиты для перевода:</b>\n"
        f"<code>{PAYMENT_CARD}</code>\n\n"
        "💡 <i>Нажмите на номер карты выше, чтобы скопировать его.</i>\n\n"
        "После перевода нажмите кнопку <b>«✅ Я оплатил»</b> ниже."
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=payment_keyboard(
            days,
            devices
        )
    )

    await callback.answer()


# =========================================================
# НАЖАТИЕ КНОПКИ «Я ОПЛАТИЛ»
# =========================================================

@dp.callback_query(
    F.data.startswith("paid_")
)
async def paid_handler(
    callback: types.CallbackQuery
):
    if not await check_user(callback):
        return

    try:
        parts = callback.data.split("_")
        days = int(parts[1])
        devices = int(parts[2])
    except (
        ValueError,
        IndexError
    ):
        await callback.answer(
            "Ошибка данных оплаты.",
            show_alert=True
        )
        return

    base_price = PLANS.get(days)
    multiplier = DEVICE_MULTIPLIERS.get(devices)

    if base_price is None or multiplier is None:
        await callback.answer(
            "Ошибка тарифа.",
            show_alert=True
        )
        return

    amount = int(base_price * multiplier)
    user_id = callback.from_user.id

    purchase_id = create_purchase(
        user_id,
        days,
        devices,
        amount
    )

    username = callback.from_user.username
    if username:
        username_text = f"@{username}"
    else:
        username_text = "нет username"

    admin_text = (
        "💳 <b>НОВАЯ ЗАЯВКА НА ОПЛАТУ</b>\n\n"
        f"👤 Имя: {callback.from_user.first_name}\n"
        f"🔗 Username: {username_text}\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"📅 Срок: <b>{days} дней</b>\n"
        f"📱 Устройств: <b>{devices}</b>\n"
        f"💰 Сумма: <b>{amount} ₽</b>\n\n"
        f"🧾 Заявка № <code>{purchase_id}</code>\n\n"
        "Выберите действие:"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            admin_text,
            parse_mode="HTML",
            reply_markup=admin_keyboard(
                purchase_id,
                user_id
            )
        )
    except Exception as e:
        logging.error(
            f"Ошибка отправки сообщения администратору: {e}"
        )

    text = (
        "⏳ <b>Оплата отправлена на проверку.</b>\n\n"
        "Администратор проверяет поступление средств.\n\n"
        "Пожалуйста, ожидайте подтверждения."
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button()
    )

    await callback.answer(
        "Заявка успешно отправлена ✅"
    )


# =========================================================
# АДМИНКА: ПРИНЯТЬ ОПЛАТУ
# =========================================================

@dp.callback_query(
    F.data.startswith("accept_")
)
async def accept_handler(
    callback: types.CallbackQuery
):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True
        )
        return

    try:
        parts = callback.data.split("_")
        purchase_id = int(parts[1])
        user_id = int(parts[2])
    except (
        ValueError,
        IndexError
    ):
        await callback.answer(
            "Ошибка данных.",
            show_alert=True
        )
        return

    current_status = get_purchase_status(
        purchase_id
    )

    if current_status != "pending":
        await callback.answer(
            "Эта заявка уже обработана.",
            show_alert=True
        )
        return

    update_purchase(
        purchase_id,
        "accepted"
    )

    try:
        await bot.send_message(
            user_id,
            "✅ <b>Оплата подтверждена!</b>\n\n"
            "Ваша подписка AuraVPN успешно активирована.",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(
            f"Ошибка отправки уведомления пользователю: {e}"
        )

    try:
        updated_text = (
            callback.message.text
            + "\n\n"
            "━━━━━━━━━━━━━━\n"
            "✅ <b>СТАТУС: ОПЛАТА ПРИНЯТА</b>"
        )
        await callback.message.edit_text(
            updated_text,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(
            f"Ошибка обновления сообщения админа: {e}"
        )

    await callback.answer(
        "Оплата принята ✅"
    )


# =========================================================
# АДМИНКА: ОТКЛОНИТЬ И ЗАБЛОКИРОВАТЬ
# =
