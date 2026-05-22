import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# =========================
# загрузка .env
# =========================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
UMONEY_CARD = os.getenv("UMONEY_CARD", "0000 0000 0000 0000")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# временная БД
# =========================
referrals_db = {}


def get_user_data(user_id: int):
    if user_id not in referrals_db:
        referrals_db[user_id] = {"referrals": set(), "balance": 0.0}
    return referrals_db[user_id]


# =========================
# клавиатура
# =========================
def main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💳 Купить VPN", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="💰 Заработать с AuraVPN", callback_data="earn"))
    kb.row(types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    return kb.as_markup()


# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    user_id = message.from_user.id

    get_user_data(user_id)

    # рефералка
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
                            "🎉 Новый пользователь по вашей ссылке!"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass

    await message.answer(
        "🏠 Главное меню\n\n"
        "👋 Добро пожаловать в AuraVPN\n"
        "🌐 Быстрый VPN без ограничений\n\n"
        "Выберите действие:",
        reply_markup=main_kb()
    )


# =========================
# ПРОФИЛЬ
# =========================
@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user = callback.from_user
    data = get_user_data(user.id)

    text = (
        f"👤 Ваш профиль\n\n"
        f"📝 Имя: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📅 Подписка: не активна\n"
        f"👥 Рефералы: {len(data['referrals'])}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


# =========================
# ЗАРАБОТОК
# =========================
@dp.callback_query(F.data == "earn")
async def earn(callback: types.CallbackQuery):
    user = callback.from_user
    bot_info = await bot.get_me()

    data = get_user_data(user.id)

    ref_link = f"https://t.me/{bot_info.username}?start={user.id}"

    text = (
        "💰 Партнёрская программа\n\n"
        "Приглашай друзей и получай %\n\n"
        f"👥 Рефералов: {len(data['referrals'])}\n"
        f"💸 Баланс: {data['balance']}₽\n\n"
        f"🔗 Твоя ссылка:\n{ref_link}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


# =========================
# BACK
# =========================
@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=main_kb()
    )
    await callback.answer()


# =========================
# запуск бота
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
