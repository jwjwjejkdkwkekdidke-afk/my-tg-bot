import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
UMONEY_CARD = os.getenv("UMONEY_CARD", "0000 0000 0000 0000")
SUPPORT_USER = os.getenv("SUPPORT_USER", "@support")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

bot = Bot(token=TOKEN)
dp = Dispatcher()


def main_kb():
    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="💳 Купить подписку",
        callback_data="buy"
    ))

    kb.row(types.InlineKeyboardButton(
        text="👤 Мой профиль",
        callback_data="profile"
    ))

    kb.row(types.InlineKeyboardButton(
        text="⚡️ Подключиться",
        callback_data="connect"
    ))

    kb.row(types.InlineKeyboardButton(
        text="📦 Остальное",
        callback_data="other"
    ))

    return kb.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):

    text = (
        "👋 Добро пожаловать в AuraVPN\n\n"
        "🌐 VPN без ограничений\n"
        "📍 Быстрые сервера\n\n"
        "Выберите действие ниже."
    )

    await message.answer(
        text,
        reply_markup=main_kb()
    )


@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):

    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="🗓 1 месяц — 120₽",
        callback_data="pay_120"
    ))

    kb.row(types.InlineKeyboardButton(
        text="🗓 3 месяца — 500₽",
        callback_data="pay_500"
    ))

    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back"
    ))

    await callback.message.edit_text(
        "💳 Выберите тариф:",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: types.CallbackQuery):

    amount = callback.data.split("_")[1]

    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="✅ Я оплатил",
        callback_data=f"check_{amount}"
    ))

    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="buy"
    ))

    await callback.message.edit_text(
        f"💳 Оплата: {amount}₽\n\n"
        f"Карта:\n{UMONEY_CARD}\n\n"
        "После оплаты нажмите кнопку ниже.",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("check_"))
async def check(callback: types.CallbackQuery):

    amount = callback.data.split("_")[1]
    user = callback.from_user

    await callback.message.answer(
        f"✅ Заявка отправлена.\n\n"
        f"Отправьте чек: {SUPPORT_USER}"
    )

    await bot.send_message(
        ADMIN_ID,
        f"Новая оплата\n\n"
        f"Пользователь: {user.full_name}\n"
        f"ID: {user.id}\n"
        f"Сумма: {amount}₽"
    )

    await callback.answer()


@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):

    await callback.message.answer(
        f"👤 Ваш ID: {callback.from_user.id}"
    )

    await callback.answer()


@dp.callback_query(F.data == "connect")
async def connect(callback: types.CallbackQuery):

    await callback.message.answer(
        "Скачайте HappVpn и вставьте ключ."
    )

    await callback.answer()


@dp.callback_query(F.data == "other")
async def other(callback: types.CallbackQuery):

    await callback.message.answer(
        f"Поддержка: {SUPPORT_USER}"
    )

    await callback.answer()


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_kb()
    )

    await callback.answer()


async def main():

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
