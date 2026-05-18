import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
UMONEY_CARD = os.getenv("UMONEY_CARD", "0000 0000 0000 0000")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

bot = Bot(token=TOKEN)
dp = Dispatcher()


def main_kb():
    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(
        text="💳 Купить VPN",
        callback_data="buy"
    ))

    kb.row(types.InlineKeyboardButton(
        text="⚡️ Подключиться",
        callback_data="connect"
    ))

    # Добавляем кнопку профиля в главное меню
    kb.row(types.InlineKeyboardButton(
        text="👤 Профиль",
        callback_data="profile"
    ))

    return kb.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):

    text = (
        "👋 Добро пожаловать в AuraVPN\n\n"
        "🌐 Быстрый VPN без ограничений\n"
        "📍 Стабильные сервера\n\n"
        "Выберите действие ниже."
    )

    await message.answer(
        text,
        reply_markup=main_kb()
    )


# Хэндлер для отображения профиля пользователя
@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user = callback.from_user
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back"
    ))

    profile_text = (
        f"👤 *Ваш профиль:*\n\n"
        f"📝 Имя: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📅 Подписка: Не активна"
    )

    await callback.message.edit_text(
        profile_text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


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
        "💳 Выберите тариф VPN:",
        reply_markup=kb.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: types.CallbackQuery):

    amount = callback.
