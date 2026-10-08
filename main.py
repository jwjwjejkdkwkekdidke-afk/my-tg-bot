import os
import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")

ADMIN_ID = 8052913358

PAYMENT_CARD = "2204128123651537"

DB_FILE = "auravpn.db"


# =========================================================
# ЦЕНЫ
# =========================================================

PLANS = {
    "7": 39,
    "30": 99,
    "90": 279,
    "180": 549,
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

def db_connect():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
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


def save_user(user: types.User):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username or "",
        user.first_name or ""
    ))

    conn.commit()
    conn.close()


def is_banned(user_id: int):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM banned_users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result is not None


def ban_user(user_id: int):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def create_purchase(user_id, days, devices, amount):
    conn = db_connect()
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


def update_purchase_status(purchase_id, status):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE purchases
        SET status = ?
        WHERE id = ?
    """, (
        status,
        purchase_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# БОТ
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def main_menu():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔐 Мой VPN",
        callback_data="my_vpn"
    )

    builder.button(
        text="💳 Купить подписку",
        callback_data="buy"
    )

    builder.button(
        text="📱 Устройства",
        callback_data="devices"
    )

    builder.button(
        text="🎁 Пригласить друга",
        callback_data="referral"
    )

    builder.button(
        text="💬 Поддержка",
        callback_data="support"
    )

    builder.button(
        text="ℹ️ О сервисе",
        callback_data="about"
    )

    builder.adjust(2, 2, 2)

    return builder.as_markup()


# =========================================================
# КНОПКА НАЗАД
# =========================================================

def back_menu():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )

    return builder.as_markup()


# =========================================================
# МЕНЮ ПОКУПКИ
# =========================================================

def plans_menu():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="7 дней — 39 ₽",
        callback_data="plan:7"
    )

    builder.button(
        text="30 дней — 99 ₽",
        callback_data="plan:30"
    )

    builder.button(
        text="90 дней — 279 ₽",
        callback_data="plan:90"
    )

    builder.button(
        text="180 дней — 549 ₽",
        callback_data="plan:180"
    )

    builder.button(
        text="⬅️ Назад",
        callback_data="main_menu"
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()


# =========================================================
# ВЫБОР УСТРОЙСТВ
# =========================================================

def devices_menu(days):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📱 1 устройство",
        callback_data=f"device:{days}:1"
    )

    builder.button(
        text="📱 3 устройства",
        callback_data=f"device:{days}:3"
    )

    builder.button(
        text="📱 5 устройств",
        callback_data=f"device:{days}:5"
    )

    builder.button(
        text="⬅️ Назад",
        callback_data="buy"
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# АДМИНСКИЕ КНОПКИ
# =========================================================

def admin_payment_keyboard(purchase_id, user_id):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Принять",
        callback_data=f"accept:{purchase_id}:{user_id}"
    )

    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject:{purchase_id}:{user_id}"
    )

    builder.adjust(2)

    return builder.as_markup()


# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):

    user = message.from_user

    save_user(user)

    if is_banned(user.id):
        await message.answer(
            "❌ Вы заблокированы.\n\n"
            "Доступ к AuraVPN для вашего аккаунта закрыт."
        )
        return

    await message.answer(
        "✨ <b>Добро пожаловать в AuraVPN!</b>\n\n"
        "🔐 Быстрый и стабильный VPN\n"
        "🌍 Доступ к сайтам и сервисам\n"
        "⚡ Простое подключение\n\n"
        "Выберите нужный раздел ниже:",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

@dp.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "✨ <b>AuraVPN</b>\n\n"
        "🔐 Ваш личный VPN-сервис\n\n"
        "Выберите нужный раздел:",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

    await callback.answer()


# =========================================================
# МОЙ VPN
# =========================================================

@dp.callback_query(F.data == "my_vpn")
async def my_vpn_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "🔐 <b>Мой VPN</b>\n\n"
        "На данный момент активный VPN-ключ не найден.\n\n"
        "💳 Чтобы получить доступ, приобретите подписку.",
        parse_mode="HTML",
        reply_markup=back_menu()
    )

    await callback.answer()


# =========================================================
# ПОКУПКА
# =========================================================

@dp.callback_query(F.data == "buy")
async def buy_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "💳 <b>Покупка AuraVPN</b>\n\n"
        "Выберите срок подписки:",
        parse_mode="HTML",
        reply_markup=plans_menu()
    )

    await callback.answer()


# =========================================================
# ВЫБОР СРОКА
# =========================================================

@dp.callback_query(F.data.startswith("plan:"))
async def plan_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    days = int(callback.data.split(":")[1])
    price = PLANS[days]

    await callback.message.edit_text(
        f"💳 <b>Подписка на {days} дней</b>\n\n"
        f"Стоимость: <b>{price} ₽</b>\n\n"
        "📱 Теперь выберите количество устройств:",
        parse_mode="HTML",
        reply_markup=devices_menu(days)
    )

    await callback.answer()


# =========================================================
# ВЫБОР УСТРОЙСТВ
# =========================================================

@dp.callback_query(F.data.startswith("device:"))
async def device_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    parts = callback.data.split(":")

    days = int(parts[1])
    devices = int(parts[2])

    price = PLANS[days]

    await callback.message.edit_text(
        "💳 <b>Оплата AuraVPN</b>\n\n"
        f"📅 Срок: <b>{days} дней</b>\n"
        f"📱 Устройства: <b>{devices}</b>\n"
        f"💰 Сумма: <b>{price} ₽</b>\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "💳 <b>Реквизиты для оплаты:</b>\n\n"
        f"<code>{PAYMENT_CARD}</code>\n\n"
        "После оплаты нажмите кнопку ниже.",
        parse_mode="HTML",
        reply_markup=payment_keyboard(days, devices)
    )

    await callback.answer()


# =========================================================
# КНОПКА ОПЛАТЫ
# =========================================================

def payment_keyboard(days, devices):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Я оплатил",
        callback_data=f"paid:{days}:{devices}"
    )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"plan:{days}"
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# Я ОПЛАТИЛ
# =========================================================

@dp.callback_query(F.data.startswith("paid:"))
async def paid_handler(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    if is_banned(user_id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    parts = callback.data.split(":")

    days = int(parts[1])
    devices = int(parts[2])

    amount = PLANS[days]

    purchase_id = create_purchase(
        user_id,
        days,
        devices,
        amount
    )

    username = callback.from_user.username

    username_text = (
        f"@{username}"
        if username
        else "нет username"
    )

    admin_text = (
        "💳 <b>НОВАЯ ОПЛАТА</b>\n\n"
        f"👤 Пользователь: {callback.from_user.first_name}\n"
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
            reply_markup=admin_payment_keyboard(
                purchase_id,
                user_id
            )
        )

    except Exception as e:
        logging.error(
            f"Ошибка отправки заявки админу: {e}"
        )

    await callback.message.edit_text(
        "⏳ <b>Платёж отправлен на проверку.</b>\n\n"
        "Администратор проверит оплату и подтвердит вашу подписку.\n\n"
        "Пожалуйста, ожидайте.",
        parse_mode="HTML",
        reply_markup=back_menu()
    )

    await callback.answer(
        "Оплата отправлена на проверку ✅"
    )


# =========================================================
# ПРИНЯТЬ ОПЛАТУ
# =========================================================

@dp.callback_query(F.data.startswith("accept:"))
async def accept_handler(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    parts = callback.data.split(":")

    purchase_id = int(parts[1])
    user_id = int(parts[2])

    update_purchase_status(
        purchase_id,
        "accepted"
    )

    try:
        await bot.send_message(
            user_id,
            "✅ <b>Оплата подтверждена!</b>\n\n"
            "Ваша подписка AuraVPN активирована.\n\n"
            "🔐 Откройте раздел «Мой VPN», "
            "чтобы получить информацию о подключении.",
            parse_mode="HTML"
        )

    except Exception as e:
        logging.error(
            f"Не удалось уведомить пользователя: {e}"
        )

    try:
        await callback.message.edit_text(
            callback.message.text
            + "\n\n"
            "━━━━━━━━━━━━━━\n"
            "✅ <b>ОПЛАТА ПРИНЯТА</b>",
            parse_mode="HTML"
        )

    except Exception:
        pass

    await callback.answer(
        "Оплата принята ✅"
    )


# =========================================================
# ОТКЛОНИТЬ = ЗАБЛОКИРОВАТЬ
# =========================================================

@dp.callback_query(F.data.startswith("reject:"))
async def reject_handler(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    parts = callback.data.split(":")

    purchase_id = int(parts[1])
    user_id = int(parts[2])

    # Меняем статус покупки
    update_purchase_status(
        purchase_id,
        "rejected"
    )

    # Блокируем пользователя навсегда
    ban_user(user_id)

    # Сообщаем пользователю
    try:
        await bot.send_message(
            user_id,
            "❌ <b>Ваша заявка отклонена.</b>\n\n"
            "Доступ к AuraVPN для вашего аккаунта "
            "заблокирован.",
            parse_mode="HTML"
        )

    except Exception as e:
        logging.error(
            f"Не удалось уведомить пользователя: {e}"
        )

    # Убираем кнопки и показываем статус админу
    try:
        await callback.message.edit_text(
            callback.message.text
            + "\n\n"
            "━━━━━━━━━━━━━━\n"
            "❌ <b>ОПЛАТА ОТКЛОНЕНА</b>\n"
            "🚫 <b>ПОЛЬЗОВАТЕЛЬ ЗАБЛОКИРОВАН</b>",
            parse_mode="HTML"
        )

    except Exception:
        pass

    await callback.answer(
        "Пользователь заблокирован ❌"
    )


# =========================================================
# УСТРОЙСТВА
# =========================================================

@dp.callback_query(F.data == "devices")
async def devices_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "📱 <b>Устройства</b>\n\n"
        "AuraVPN можно использовать на разных устройствах.\n\n"
        "Выберите подходящий тариф при покупке "
        "подписки.",
        parse_mode="HTML",
        reply_markup=back_menu()
    )

    await callback.answer()


# =========================================================
# РЕФЕРАЛЬНАЯ СИСТЕМА
# =========================================================

@dp.callback_query(F.data == "referral")
async def referral_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}"
        f"?start=ref_{callback.from_user.id}"
    )

    await callback.message.edit_text(
        "🎁 <b>Пригласить друга</b>\n\n"
        "Приглашайте друзей в AuraVPN "
        "по своей ссылке.\n\n"
        "🔗 Ваша ссылка:\n"
        f"<code>{referral_link}</code>",
        parse_mode="HTML",
        reply_markup=back_menu()
    )

    await callback.answer()


# =========================================================
# ПОДДЕРЖКА
# =========================================================

@dp.callback_query(F.data == "support")
async def support_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "💬 <b>Поддержка AuraVPN</b>\n\n"
        "Если у вас возникли проблемы с оплатой "
        "или подключением, обратитесь к администратору.\n\n"
        "После обращения укажите свой Telegram ID.",
        parse_mode="HTML",
        reply_markup=back_menu()
    )

    await callback.answer()


# =========================================================
# О СЕРВИСЕ
# =========================================================

@dp.callback_query(F.data == "about")
async def about_handler(callback: types.CallbackQuery):

    if is_banned(callback.from_user.id):
        await callback.answer(
            "❌ Вы заблокированы.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "ℹ️ <b>О AuraVPN</b>\n\n"
        "AuraVPN — сервис для безопасного "
        "и удобного доступа к интернету.\n\n"
        "🔐 Защита соединения\n"
        "⚡ Быстрое подключение\n"
        "🌍 Доступ к нужным ресурсам\n"
        "📱 Поддержка нескольких устройств",
        parse_mode="HTML",
        reply_markup=back_menu()
    )

    await callback.answer()


# =========================================================
# ОБЫЧНЫЕ СООБЩЕНИЯ
# =========================================================

@dp.message()
async def all_messages_handler(message: types.Message):

    user_id = message.from_user.id

    save_user(message.from_user)

    if is_banned(user_id):
        await message.answer(
            "❌ Вы заблокированы и не можете "
            "пользоваться этим ботом."
        )
        return

    # Администраторские сообщения не обрабатываем
    if user_id == ADMIN_ID:
        return

    await message.answer(
        "🏠 Используйте кнопки меню ниже:",
        reply_markup=main_menu()
    )


# =========================================================
# ЗАПУСК
# =========================================================

async def main():

    init_db()

    logging.info("AuraVPN запускается...")

    try:
        await bot.delete_webhook(
            drop_pending_updates=True
        )
    except Exception as e:
        logging.warning(
            f"Webhook: {e}"
        )

    logging.info("AuraVPN запущен!")

    await dp.start_polling(bot)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен.")
