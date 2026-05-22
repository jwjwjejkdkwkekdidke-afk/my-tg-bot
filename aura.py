import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = "TOKEN_BOT"

ADMIN_ID = 123456789

PAYMENT_INFO = """
💳 Оплата через СБП / карту

🏦 Сбербанк:
0000 0000 0000 0000

👤 Получатель:
DAMIR

⚠️ После оплаты нажмите кнопку «Я оплатил»
"""

VPN_KEY = "https://raw.githubusercontent.com/Temnuk/naabuzil/refs/heads/main/whitelist_full"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ХРАНЕНИЕ ПОДПИСОК
subscriptions = {}

# ТАРИФЫ
TARIFFS = {
    "39": "7 дней",
    "99": "30 дней",
    "279": "90 дней",
    "549": "180 дней"
}


def main_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="💳 Купить VPN",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⚡️ Подключение",
            callback_data="connect"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="👤 Профиль",
            callback_data="profile"
        )
    )

    return kb.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):

    text = (
        "🌐 *AuraVPN*\n\n"
        "🚀 Быстрый VPN без ограничений\n"
        "📱 Работает в РФ\n"
        "⚡️ Высокая скорость\n"
        "🔒 Безопасное подключение\n\n"
        "Выберите действие ниже."
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=main_kb()
    )


@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):

    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="📅 7 дней — 39₽",
        callback_data="pay_39"
    ))

    kb.row(types.InlineKeyboardButton(
        text="📅 30 дней — 99₽",
        callback_data="pay_99"
    ))

    kb.row(types.InlineKeyboardButton(
        text="📅 90 дней — 279₽",
        callback_data="pay_279"
    ))

    kb.row(types.InlineKeyboardButton(
        text="📅 180 дней — 549₽",
        callback_data="pay_549"
    ))

    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back"
    ))

    await callback.message.edit_text(
        "💳 *Выберите тариф VPN:*",
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: types.CallbackQuery):

    amount = callback.data.split("_")[1]

    tariff = TARIFFS.get(amount)

    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="✅ Я оплатил",
        callback_data=f"check_{amount}"
    ))

    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="buy"
    ))

    text = (
        f"💳 *Оплата VPN*\n\n"
        f"📦 Тариф: {tariff}\n"
        f"💰 Сумма: {amount}₽\n\n"
        f"{PAYMENT_INFO}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("check_"))
async def check(callback: types.CallbackQuery):

    amount = callback.data.split("_")[1]

    tariff = TARIFFS.get(amount)

    user = callback.from_user

    await callback.message.edit_text(
        "⏳ *Проверяем оплату...*\n\n"
        "Обычно это занимает до 5 минут.",
        parse_mode="Markdown"
    )

    admin_kb = InlineKeyboardBuilder()

    admin_kb.row(
        types.InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=f"accept_{user.id}_{amount}"
        ),

        types.InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"decline_{user.id}"
        )
    )

    await bot.send_message(
        ADMIN_ID,

        f"💸 *Новая заявка*\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📦 Тариф: {tariff}\n"
        f"💰 Сумма: {amount}₽",

        parse_mode="Markdown",
        reply_markup=admin_kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("accept_"))
async def admin_accept(callback: types.CallbackQuery):

    data = callback.data.split("_")

    user_id = int(data[1])

    amount = data[2]

    tariff = TARIFFS.get(amount)

    subscriptions[user_id] = tariff

    try:

        await bot.send_message(
            user_id,

            f"✅ *Оплата подтверждена!*\n\n"
            f"📦 Тариф: {tariff}\n\n"
            f"🔑 *Ваш VPN ключ:*\n"
            f"`{VPN_KEY}`\n\n"
            f"📲 Откройте HappVPN\n"
            f"➜ Импортируйте подписку\n"
            f"➜ Вставьте ссылку\n\n"
            f"🚀 VPN успешно активирован.",

            parse_mode="Markdown"
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"🟢 *Статус: Оплачено*",
            parse_mode="Markdown"
        )

    except Exception as e:

        await callback.message.reply(
            f"❌ Ошибка:\n{e}"
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("decline_"))
async def admin_decline(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    try:

        await bot.send_message(
            user_id,

            "❌ *Оплата отклонена*\n\n"
            "Если вы оплатили VPN — напишите администратору.",

            parse_mode="Markdown"
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"🔴 *Статус: Отклонено*",

            parse_mode="Markdown"
        )

    except Exception as e:

        await callback.message.reply(
            f"❌ Ошибка:\n{e}"
        )

    await callback.answer()


@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):

    user = callback.from_user

    sub = subscriptions.get(user.id, "Не активна")

    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back"
    ))

    text = (
        f"👤 *Ваш профиль*\n\n"
        f"📝 Имя: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📦 Подписка: {sub}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data == "connect")
async def connect(callback: types.CallbackQuery):

    text = (
        "📲 *Как подключить VPN*\n\n"
        "1️⃣ Скачайте HappVPN\n"
        "2️⃣ Нажмите «Импорт подписки»\n"
        "3️⃣ Вставьте полученный ключ\n"
        "4️⃣ Подключитесь к серверу\n\n"
        "🚀 Готово."
    )

    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back"
    ))

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "🏠 *Главное меню*",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

    await callback.answer()


async def main():

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
