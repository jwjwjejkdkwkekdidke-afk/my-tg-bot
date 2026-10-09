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
    ReplyKeyboardRemove,
    FSInputFile
)


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН")
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
    cur.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None


def ban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def create_purchase(user_id: int, days: int, devices: int, amount: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO purchases (user_id, days, devices, amount, status)
        VALUES (?, ?, ?, ?, 'pending')
    """, (user_id, days, devices, amount))
    purchase_id = cur.lastrowid
    conn.commit()
    conn.close()
    return purchase_id


def update_purchase(purchase_id: int, status: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE purchases SET status = ? WHERE id = ?", (status, purchase_id))
    conn.commit()
    conn.close()


def get_purchase_status(purchase_id: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT status FROM purchases WHERE id = ?", (purchase_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None


# =========================================================
# ИНИЦИАЛИЗАЦИЯ БОТА И ДИСПЕТЧЕРА
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# КЛАВИАТУРЫ И ТЕКСТЫ
# =========================================================

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню"), KeyboardButton(text="💳 Купить подписку")],
            [KeyboardButton(text="🔐 Мой VPN"), KeyboardButton(text="📱 Устройства")],
            [KeyboardButton(text="🎁 Пригласить друга"), KeyboardButton(text="💬 Поддержка")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔐 Мой VPN", callback_data="menu_vpn")
    builder.button(text="💳 Купить подписку", callback_data="menu_buy")
    builder.button(text="📱 Устройства", callback_data="menu_devices")
    builder.button(text="🎁 Пригласить друга", callback_data="menu_referral")
    builder.button(text="💬 Поддержка", callback_data="menu_support")
    builder.button(text="ℹ️ О сервисе", callback_data="menu_about")
    builder.button(text="🔽 Открыть панель", callback_data="hide_panel")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def welcome_text():
    return (
        "✨ <b>Добро пожаловать в AuraVPN!</b>\n\n"
        "🔐 Быстрый и стабильный VPN\n"
        "🌍 Доступ к нужным сайтам и сервисам\n"
        "⚡ Простое подключение\n\n"
        "<b>Выберите нужный раздел:</b>"
    )


def about_text():
    return (
        "ℹ️ <b>О сервисе AuraVPN</b>\n\n"
        "<b>AuraVPN</b> — это ваш надежный инструмент для безопасного, анонимного и свободного интернета.\n\n"
        "🚀 <b>Наши преимущества:</b>\n"
        "• <b>Высокая скорость</b> — комфортный просмотр видео, игры и работа без задержек.\n"
        "• <b>Стабильность</b> — современные протоколы подключения, которые не подводят.\n"
        "• <b>Безопасность</b> — надежное шифрование данных и полная конфиденциальность.\n"
        "• <b>Удобство</b> — легкая настройка на любых устройствах за пару кликов.\n\n"
        "Остались вопросы? Обратитесь в раздел поддержки!"
    )


def support_text():
    return (
        "💬 <b>Служба поддержки AuraVPN</b>\n\n"
        "Столкнулись с трудностями при оплате, настройке или подключении VPN?\n\n"
        "✍️ <b>Как с нами связаться:</b>\n"
        "Напишите ваш вопрос или суть проблемы ответным сообщением (или обратитесь напрямую к администратору). Пожалуйста, укажите ваш <b>ID</b> и приложите скриншот, если это необходимо.\n\n"
        "Мы постараемся помочь вам в самое ближайшее время!"
    )


def back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Главное меню", callback_data="main_menu")
    return builder.as_markup()


def plans_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="7 дней — 39 ₽", callback_data="plan_7")
    builder.button(text="30 дней — 99 ₽", callback_data="plan_30")
    builder.button(text="90 дней — 279 ₽", callback_data="plan_90")
    builder.button(text="180 дней — 549 ₽", callback_data="plan_180")
    builder.button(text="⬅️ Главное меню", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def devices_keyboard(days: int):
    builder = InlineKeyboardBuilder()
    base_price = PLANS[days]
    for dev_count, multiplier in DEVICE_MULTIPLIERS.items():
        price = int(base_price * multiplier)
        builder.button(text=f"📱 {dev_count} устр. — {price} ₽", callback_data=f"device_{days}_{dev_count}")
    builder.button(text="⬅️ Назад", callback_data="menu_buy")
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard(days: int, devices: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{days}_{devices}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"plan_{days}"))
    return builder.as_markup()


def admin_keyboard(purchase_id: int, user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"accept_{purchase_id}_{user_id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_{purchase_id}_{user_id}")
    builder.adjust(2)
    return builder.as_markup()


async def check_user(callback: types.CallbackQuery) -> bool:
    if is_banned(callback.from_user.id):
        await callback.answer("❌ Вы заблокированы.", show_alert=True)
        return False
    return True


# =========================================================
# ОБРАБОТЧИКИ КОМАНД И КНОПОК
# =========================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы и не можете пользоваться ботом.")
        return
    photo = FSInputFile("welcome.png")[cite: 1]
    await message.answer_photo(photo=photo, caption=welcome_text(), parse_mode="HTML", reply_markup=main_menu())


@dp.callback_query(F.data == "hide_panel")
async def hide_panel_handler(callback: types.CallbackQuery):
    if not await check_user(callback):
        return

    await callback.message.answer("🔽 Нижняя панель свернута.", reply_markup=ReplyKeyboardRemove())

    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Открыть панель", callback_data="show_panel")
    builder.button(text="⬅️ Главное меню", callback_data="main_menu")
    builder.adjust(1)

    text = (
        "🔽 <b>Панель свернута</b>\n\n"
        "Нижняя клавиатура убрана с экрана. Вы можете вернуть её в любой момент."
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    photo = FSInputFile("welcome.png")[cite: 1]
    await callback.message.answer_photo(photo=photo, caption=text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer("Панель скрыта ✅")


@dp.callback_query(F.data == "show_panel")
async def show_panel_handler(callback: types.CallbackQuery):
    if not await check_user(callback):
        return

    await callback.message.answer("📱 Нижняя панель снова активирована:", reply_markup=bottom_keyboard())
    try:
        await callback.message.delete()
    except Exception:
        pass
    photo = FSInputFile("welcome.png")[cite: 1]
    await callback.message.answer_photo(photo=photo, caption=welcome_text(), parse_mode="HTML", reply_markup=main_menu())
    await callback.answer("Панель возвращена ✅")


@dp.message(F.text == "🏠 Главное меню")
async def bottom_main_menu(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return
    await message.answer("🏠 Главное меню:", reply_markup=bottom_keyboard())
    photo = FSInputFile("welcome.png")[cite: 1]
    await message.answer_photo(photo=photo, caption=welcome_text(), parse_mode="HTML", reply_markup=main_menu())


@dp.message(F.text == "💳 Купить подписку")
async def bottom_buy(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return
    photo = FSInputFile("subscribe.png")[cite: 1]
    await message.answer_photo(photo=photo, caption="💳 <b>Покупка AuraVPN</b>\n\nВыберите срок подписки:", parse_mode="HTML", reply_markup=plans_keyboard())


@dp.message(F.text == "🔐 Мой VPN")
async def bottom_vpn(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return
    photo = FSInputFile("about.png")[cite: 1]
    await message.answer_photo(photo=photo, caption="🔐 <b>Мой VPN</b>\n\nАктивная подписка не найдена.", parse_mode="HTML", reply_markup=back_button())


@dp.message(F.text == "📱 Устройства")
async def bottom_devices(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы.")
        return
    photo = FSInputFile("about.png")[cite: 1]
    await message.answer_photo(photo=photo, caption="📱 <b>Устройства</b>\n\nКоличество устройств выбирается при покупке.", parse_mode="HTML", reply_markup=back_button())


@dp.message(F.text == "🎁 Пригласить друга")
async def bottom_referral(message: types.Message):
    if is_banned
