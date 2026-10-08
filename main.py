```python
import os
import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ============================================================
# НАСТРОЙКИ
# ============================================================

logging.basicConfig(level=logging.INFO)

TOKEN = (
    os.getenv("MY_BOT_TOKEN")
    or os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("TOKEN")
)

UMONEY_CARD = os.getenv("UMONEY_CARD", "2204128123651537")

# ID администратора
ADMIN_ID = 8052913358

if not TOKEN:
    raise ValueError(
        "ОШИБКА: Токен бота не найден в переменных окружения хостинга!"
    )


bot = Bot(token=TOKEN)
dp = Dispatcher()


# ============================================================
# SQLITE — БАЗА ЗАБЛОКИРОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

DB_FILE = "auravpn.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()


def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM banned_users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def ban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def unban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM banned_users WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()


# ============================================================
# ВРЕМЕННАЯ БАЗА РЕФЕРАЛОВ
# ============================================================

referrals_db = {}

# Временное хранение выбора пользователя
# при оформлении покупки
user_checkout = {}


def get_user_data(user_id: int):
    if user_id not in referrals_db:
        referrals_db[user_id] = {
            "referrals": set(),
            "balance": 0.0
        }

    return referrals_db[user_id]


# ============================================================
# КЛАВИАТУРЫ
# ============================================================

def main_reply_kb():
    builder = ReplyKeyboardBuilder()

    builder.button(text="🏠 Главное меню")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def profile_inline_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="🔗 Подключить VPN (3 устройства)",
            callback_data="management"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⚙ Управление подпиской",
            callback_data="management"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="🛍 Купить подписку",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="💰 Заработок",
            callback_data="referral"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="💬 О сервисе",
            callback_data="info"
        ),
        types.InlineKeyboardButton(
            text="✈️ Поддержка",
            callback_data="support"
        )
    )

    return kb.as_markup()


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

def get_main_menu_text():
    return (
        "✨ *Добро пожаловать в AuraVPN*\n\n"
        "💬 *Надёжный VPN без логов, без ограничений "
        "по скорости и трафику.*\n\n"
        "⬇️ Выберите раздел в меню ниже:"
    )


# ============================================================
# ПРОВЕРКА БАНА
# ============================================================

async def check_banned_message(message: types.Message) -> bool:
    user_id = message.from_user.id

    if is_banned(user_id):
        await message.answer(
            "🚫 *Доступ к AuraVPN заблокирован.*\n\n"
            "Вы не можете пользоваться этим ботом.",
            parse_mode="Markdown"
        )
        return True

    return False


async def check_banned_callback(callback: types.CallbackQuery) -> bool:
    user_id = callback.from_user.id

    if is_banned(user_id):
        await callback.answer(
            "🚫 Вы заблокированы.",
            show_alert=True
        )
        return True

    return False


# ============================================================
# /START
# ============================================================

@dp.message(Command("start"))
async def start_command(message: types.Message):

    if await check_banned_message(message):
        return

    user_id = message.from_user.id

    get_user_data(user_id)

    # Реферальная система
    args = message.text.split()

    if len(args) > 1:
        try:
            referrer_id = int(args[1])

            if referrer_id != user_id:

                ref_data = get_user_data(referrer_id)

                if user_id not in ref_data["referrals"]:

                    ref_data["referrals"].add(user_id)

                    try:
                        await bot.send_message(
                            referrer_id,
                            "🎉 По вашей реферальной ссылке "
                            "зарегистрировался новый пользователь!"
                        )
                    except Exception:
                        pass

        except ValueError:
            pass

    await message.answer(
        text=get_main_menu_text(),
        parse_mode="Markdown",
        reply_markup=profile_inline_kb()
    )

    await message.answer(
        "⬇️ Используйте панель меню ниже:",
        reply_markup=main_reply_kb()
    )


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

@dp.message(F.text == "🏠 Главное меню")
async def text_main_menu(message: types.Message):

    if await check_banned_message(message):
        return

    await message.answer(
        text=get_main_menu_text(),
        parse_mode="Markdown",
        reply_markup=profile_inline_kb()
    )


# ============================================================
# УПРАВЛЕНИЕ VPN
# ============================================================

@dp.callback_query(F.data == "management")
async def management_menu(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    text = (
        "🛡 *Управление VPN*\n\n"
        "Здесь вы можете проверить статус вашей подписки, "
        "посмотреть активные устройства или продлить доступ.\n\n"
        "📅 *Статус:* Активна\n"
        "📱 *Устройств подключено:* 1 / 3"
    )

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="📱 Устройства",
            callback_data="devices"
        ),
        types.InlineKeyboardButton(
            text="📅 Продлить подписку",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="back"
        )
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# УСТРОЙСТВА
# ============================================================

@dp.callback_query(F.data == "devices")
async def devices_menu(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="➕ Подключить новое устройство",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="management"
        )
    )

    text = (
        "📱 *Ваши устройства*\n\n"
        "Активных подключений: 1"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# РЕФЕРАЛЬНАЯ ПРОГРАММА
# ============================================================

@dp.callback_query(F.data == "referral")
async def referral_menu(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    user = callback.from_user

    bot_info = await bot.get_me()

    user_data = get_user_data(user.id)

    ref_count = len(user_data["referrals"])
    ref_balance = user_data["balance"]

    ref_link = (
        f"https://t.me/{bot_info.username}?start={user.id}"
    )

    text = (
        "👥 *Реферальная программа*\n\n"
        f"🔗 *Ваша ссылка:*\n"
        f"`{ref_link}`\n\n"
        f"👥 Приглашено: *{ref_count}* чел.\n"
        f"👛 Заработано: *{ref_balance} ₽*\n\n"
        "Вы получаете *20%* с каждой покупки вашего реферала."
    )

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="💸 Вывести средства",
            callback_data="withdraw"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="back"
        )
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# ВЫВОД
# ============================================================

@dp.callback_query(F.data == "withdraw")
async def withdraw_funds(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    await callback.answer(
        "⚠️ Минимальная сумма для вывода: 150 ₽",
        show_alert=True
    )


# ============================================================
# ПОДДЕРЖКА
# ============================================================

@dp.callback_query(F.data == "support")
async def support_menu(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    text = (
        "✍️ *Напишите свой вопрос для создания тикета.*\n\n"
        "Чтобы мы могли быстрее помочь, сразу отправляйте:\n"
        "1. Описание проблемы.\n"
        "2. Скриншот ошибки / экрана при необходимости.\n"
        "3. Когда возникла проблема.\n\n"
        "Пожалуйста, *НЕ* нужно писать просто:\n"
        "«привет», «здравствуйте», «не работает» и ждать ответа.\n\n"
        "❤️ Так мы сможем быстрее проверить информацию "
        "и решить проблему."
    )

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="back"
        )
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# ИНФОРМАЦИЯ
# ============================================================

@dp.callback_query(F.data == "info")
async def info_menu(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    text = (
        "ℹ️ *Информация и правила AuraVPN*\n\n"
        "🔒 *Безопасность и конфиденциальность:*\n"
        "Мы не собираем и не храним логи вашей сетевой активности "
        "(No-Logs Policy).\n\n"
        "⚡ *Почему это не обман:*\n"
        "Сервис работает на базе современных "
        "высокоскоростных протоколов."
    )

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="back"
        )
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# ПОКУПКА
# ============================================================

@dp.callback_query(F.data == "buy")
async def buy_menu(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="📅 7 дней — 39₽",
            callback_data="term_7"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="📅 30 дней — 99₽",
            callback_data="term_30"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="📅 90 дней — 279₽",
            callback_data="term_90"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="📅 180 дней — 549₽",
            callback_data="term_180"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="back"
        )
    )

    await callback.message.edit_text(
        text="💳 *Шаг 1 из 2:* Выберите срок подписки:",
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# ВЫБОР СРОКА
# ============================================================

@dp.callback_query(F.data.startswith("term_"))
async def select_devices(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    days = callback.data.split("_")[1]

    user_checkout[callback.from_user.id] = {
        "days": days
    }

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="📱 1 устройство",
            callback_data="dev_1"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="📱📱 3 устройства",
            callback_data="dev_3"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="📱📱📱 5 устройств",
            callback_data="dev_5"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад к срокам",
            callback_data="buy"
        )
    )

    await callback.message.edit_text(
        text=(
            f"📅 Вы выбрали срок: *{days} дней*.\n\n"
            "📱 *Шаг 2 из 2:* Выберите количество устройств:"
        ),
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# ОПЛАТА
# ============================================================

@dp.callback_query(F.data.startswith("dev_"))
async def payment_process(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    devices_count = callback.data.split("_")[1]

    user_id = callback.from_user.id

    days = user_checkout.get(
        user_id,
        {}
    ).get(
        "days",
        "30"
    )

    base_prices = {
        "7": 39,
        "30": 99,
        "90": 279,
        "180": 549
    }

    base_price = base_prices.get(days, 99)

    multiplier = (
        1
        if devices_count == "1"
        else 2.5
        if devices_count == "3"
        else 4
    )

    amount = int(base_price * multiplier)

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="✅ Я оплатил",
            callback_data=f"check_{amount}"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад к выбору устройств",
            callback_data=f"term_{days}"
        )
    )

    text = (
        "💳 *Оплата VPN*\n\n"
        f"📅 Срок: *{days} дней*\n"
        f"📱 Устройств: *{devices_count}*\n"
        f"💰 Сумма к оплате: *{amount} ₽*\n\n"
        f"Карта для перевода:\n`{UMONEY_CARD}`\n\n"
        "После перевода средств нажмите кнопку ниже."
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# ЗАЯВКА НА ОПЛАТУ
# ============================================================

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    amount = callback.data.split("_")[1]

    user_id = callback.from_user.id

    username = callback.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "Без username"

    # --------------------------------------------------------
    # КНОПКИ ДЛЯ АДМИНИСТРАТОРА
    # --------------------------------------------------------

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="✅ Принять",
            callback_data=f"payment_accept_{user_id}_{amount}"
        ),
        types.InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"payment_reject_{user_id}_{amount}"
        )
    )

    # --------------------------------------------------------
    # ОТПРАВКА ЗАЯВКИ АДМИНУ
    # --------------------------------------------------------

    if ADMIN_ID:

        try:

            await bot.send_message(
                ADMIN_ID,

                "🔔 *Новая заявка на оплату!*\n\n"
                f"👤 Пользователь: {username_text}\n"
                f"🆔 ID: `{user_id}`\n"
                f"💰 Сумма: *{amount} ₽*",

                parse_mode="Markdown",
                reply_markup=kb.as_markup()
            )

        except Exception as e:

            logging.error(
                f"Ошибка отправки заявки админу: {e}"
            )

    await callback.answer(
        "✅ Заявка отправлена администратору.\n"
        "Ожидайте проверки.",
        show_alert=True
    )


# ============================================================
# АДМИН — ПРИНЯТЬ ОПЛАТУ
# ============================================================

@dp.callback_query(F.data.startswith("payment_accept_"))
async def payment_accept(callback: types.CallbackQuery):

    # Только администратор
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )
        return

    parts = callback.data.split("_")

    # payment_accept_USERID_AMOUNT
    user_id = int(parts[2])
    amount = parts[3]

    # Убираем кнопки
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    # Сообщаем админу
    await callback.answer(
        "✅ Оплата принята."
    )

    # Сообщаем пользователю
    try:

        await bot.send_message(
            user_id,

            "✅ *Оплата подтверждена!*\n\n"
            f"💰 Сумма: *{amount} ₽*\n\n"
            "Спасибо за покупку AuraVPN! ❤️",

            parse_mode="Markdown"
        )

    except Exception as e:

        logging.error(
            f"Не удалось уведомить пользователя {user_id}: {e}"
        )


# ============================================================
# АДМИН — ОТКЛОНИТЬ И ЗАБЛОКИРОВАТЬ
# ============================================================

@dp.callback_query(F.data.startswith("payment_reject_"))
async def payment_reject(callback: types.CallbackQuery):

    # Только администратор
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )
        return

    parts = callback.data.split("_")

    # payment_reject_USERID_AMOUNT
    user_id = int(parts[2])
    amount = parts[3]

    # Добавляем пользователя в постоянный бан
    ban_user(user_id)

    # Убираем кнопки с заявки
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    # Сообщение админу
    await callback.answer(
        "❌ Пользователь заблокирован.",
        show_alert=True
    )

    # Сообщение пользователю
    try:

        await bot.send_message(
            user_id,

            "🚫 *Доступ к AuraVPN заблокирован.*\n\n"
            "Вы больше не можете пользоваться ботом.",

            parse_mode="Markdown"
        )

    except Exception as e:

        logging.error(
            f"Не удалось уведомить пользователя {user_id}: {e}"
        )


# ============================================================
# ВОЗВРАТ В ГЛАВНОЕ МЕНЮ
# ============================================================

@dp.callback_query(F.data == "back")
async def back_to_main(callback: types.CallbackQuery):

    if await check_banned_callback(callback):
        return

    await callback.message.edit_text(
        text=get_main_menu_text(),
        parse_mode="Markdown",
        reply_markup=profile_inline_kb()
    )

    await callback.answer()


# ============================================================
# ЗАПУСК
# ============================================================

async def main():

    # Создаём SQLite
    init_db()

    print("BOT STARTED SUCCESSFULLY")

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
```
