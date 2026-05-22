import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN", "ТВОЙ_ТОКЕН")
UMONEY_CARD = os.getenv("UMONEY_CARD", "0000 0000 0000 0000")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных для рефералов
referrals_db = {}


def get_user_data(user_id):
    """Инициализация данных пользователя в мини-БД"""
    if user_id not in referrals_db:
        referrals_db[user_id] = {"referrals": set(), "balance": 0.0}
    return referrals_db[user_id]


def main_kb():
    """Постоянная клавиатура внизу экрана (строго 3 кнопки)"""
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="💳 Купить VPN"))
    kb.row(types.KeyboardButton(text="💰 Заработать с AuraVPN"))
    kb.row(types.KeyboardButton(text="👤 Профиль"))
    return kb.as_markup(resize_keyboard=True)


@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    user_id = message.from_user.id
    
    get_user_data(user_id)
    
    if len(args) > 1:
        referrer_id = args[1]
        try:
            referrer_id = int(referrer_id)
            if referrer_id != user_id:
                ref_data = get_user_data(referrer_id)
                if user_id not in ref_data["referrals"]:
                    ref_data["referrals"].add(user_id)
                    try:
                        await bot.send_message(
                            referrer_id, 
                            "🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass

    text = (
        "🏠 **Главное меню**\n\n"
        "👋 Добро пожаловать в AuraVPN\n"
        "🌐 Быстрый VPN без ограничений\n\n"
        "Выберите действие на клавиатуре ниже:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_kb())


# 1. РАЗДЕЛ: ПРОФИЛЬ (НАЖАТИЕ НА НИЖНЮЮ КНОПКУ)
@dp.message(F.text == "👤 Профиль")
async def profile_message(message: types.Message):
    user = message.from_user
    user_data = get_user_data(user.id)
    ref_count = len(user_data["referrals"])
    
    profile_text = (
        f"👤 *Ваш профиль:*\n\n"
        f"📝 Имя: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📅 Подписка: Не активна\n"
        f"👥 Приглашено друзей: {ref_count}"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back"))
    
    await message.answer(profile_text, parse_mode="Markdown", reply_markup=kb.as_markup())


# 2. РАЗДЕЛ: ЗАРАБОТАТЬ С AURAVPN (НАЖАТИЕ НА НИЖНЮЮ КНОПКУ)
@dp.message(F.text == "💰 Заработать с AuraVPN")
async def earn_message(message: types.Message):
    user = message.from_user
    bot_info = await bot.get_me()
    
    user_data = get_user_data(user.id)
    ref_count = len(user_data["referrals"])
    ref_balance = user_data["balance"]
    
    ref_link = f"https://t.me/{bot_info.username}?start={user.id}"

    text = (
        f"💰 *Партнерская программа AuraVPN
