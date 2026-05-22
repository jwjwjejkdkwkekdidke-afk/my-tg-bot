import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN", "ТВОЙ_ТОКЕН")
UMONEY_CARD = os.getenv("UMONEY_CARD", "0000 0000 0000 0000")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных для рефералов
referrals_db = {}


def get_user_data(user_id: int):
    """Инициализация данных пользователя в нашей мини-БД"""
    if user_id not in referrals_db:
        referrals_db[user_id] = {"referrals": set(), "balance": 0.0}
    return referrals_db[user_id]


def main_kb():
    """Главное меню бота (строго 3 кнопки)"""
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💳 Купить VPN", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="💰 Заработать с AuraVPN", callback_data="earn"))
    kb.row(types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    return kb.as_markup()


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
        "Выберите действие ниже:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_kb())


# 1. РАЗДЕЛ: ПРОФИЛЬ
@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user = callback.from_user
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
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    
    await callback.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()


# 2. РАЗДЕЛ: ЗАРАБОТАТЬ С AURAVPN
@dp.callback_query(F.data == "earn")
async def earn(callback: types.CallbackQuery):
    user = callback.from_user
    bot_info = await bot.get_me()
    
    user_data = get_user_data(user.id)
    ref_count = len(user_data["referrals"])
    ref_balance = user_data["balance"]
    
    ref_link = f"https://t.me/{bot_info.username}?start={user.id}"

    text = (
        f"💰 *Партнерская программа AuraVPN*\n\n"
        f"Приглашайте друзей и зарабатывайте 30% с каждого пополнения!\n\n"
        f"Например:\n"
        f"— Друзья перешли по вашей ссылке и потратили 1000₽\n"
        f"— Вы получаете 300.0₽ и выводите на КАРТУ/USDT!\n\n"
        f"📊 *Ваша статистика:*\n"
        f"👥 Количество приглашённых: *{ref_count}* чел.\n"
        f"💵 Ваш баланс: *{ref_balance}₽*\n\n"
        f"🔗 *Ваша реферальная ссылка:*\n"
        f"`{ref_link}`\n\n"
        f"_Нажмите на ссылку выше, чтобы скопировать её._"
    )

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()


# 3. РАЗДЕЛ: КУПИТЬ VPN (ШАГ 1: ВЫ
