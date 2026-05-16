import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Логи
logging.basicConfig(level=logging.INFO)

# ENV
TOKEN = os.getenv("TOKEN")
UMONEY_CARD = os.getenv("UMONEY_CARD")
SUPPORT_USER = os.getenv("SUPPORT_USER")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Бот
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ГЛАВНОЕ МЕНЮ ---

def main_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="💳 Купить подписку",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="👤 Мой профиль",
            callback_data="profile"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⚡️ Подключиться",
            callback_data="connect"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="📦 Остальное",
            callback_data="other"
        )
    )

    return kb.as_markup()

# --- START ---

@dp.message(Command("start"))
async def start(message: types.Message):

    text = (
        "Привет 👋 **Это AuraVPN** — твой надежный сервис ✨\n\n"
        "🌐 YouTube, Instagram, Discord без блокировок.\n"
        "📍 Локации: 🇸🇪 🇨🇭 🇪🇸 🇩🇪 🇦🇹 🇳🇱 🇬🇪\n\n"
        "Включай VPN и забудь про ограничения 🙌"
    )

    await message.answer(
        text,
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

# --- ПОКУПКА ---

@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="🗓 1 месяц — 120₽",
            callback_data="pay_120"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="🗓 3 месяца — 500₽",
            callback_data="pay_500"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back"
        )
    )

    await callback.message.edit_text(
        "💳 **Выберите тариф AuraVPN:**",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

    await callback.answer()

# --- ОПЛАТА ---

@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: types.CallbackQuery):

    summ = callback.data.split("_")[1]

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="✅ Я оплатил",
            callback_data=f"check_{summ}"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="buy"
        )
    )

    await callback.message.edit_text(
        f"💳 **Оплата: {summ}₽**\n\n"
        f"ЮMoney / Карта:\n`{UMONEY_CARD}`\n\n"
        "После оплаты нажмите кнопку ниже.",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

    await callback.answer()

# --- ПРОВЕРКА ОПЛАТЫ ---

@dp.callback_query(F.data.startswith("check_"))
async def check(callback: types.CallbackQuery):

    summ = callback.data.split("_")[1]
    user = callback.from_user

    await callback.answer(
        "Заявка отправлена!",
        show_alert=True
    )

    await callback.message.answer(
        f"⏳ **Заявка принята!**\n\n"
        f"Отправьте чек сюда: {SUPPORT_USER}",
        parse_mode="Markdown"
    )

    admin_kb = InlineKeyboardBuilder()

    admin_kb.row(
        types.InlineKeyboardButton(
            text="✅ Принять",
            callback_data=f"adm_confirm_{user.id}"
        ),
        types.InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"adm_decline_{user.id}"
        )
    )

    await bot.send_message(
        ADMIN_ID,
        f"💰 **НОВАЯ ОПЛАТА**\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"💵 Сумма: {summ}₽",
        reply_markup=admin_kb.as_markup(),
        parse_mode="Markdown"
    )

# --- ПРОФИЛЬ ---

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):

    text = (
        f"👤 **Ваш профиль**\n\n"
        f"🆔 ID: `{callback.from_user.id}`\n"
        f"📊 Статус: Не активен\n"
        f"⏳ Подписка: —"
    )

    await callback.message.answer(
        text,
        parse_mode="Markdown"
    )

    await callback.answer()

# --- ПОДКЛЮЧЕНИЕ ---

@dp.callback_query(F.data == "connect")
async def connect(callback: types.CallbackQuery):

    text = (
        "⚡️ **Как подключиться?**\n\n"
        "1️⃣ Скачайте HappVpn\n\n"
        "2️⃣ Купите подписку\n\n"
        "3️⃣ Получите ключ у поддержки\n\n"
        "4️⃣ Вставьте ключ в приложение"
    )

    await callback.message.answer(
        text,
        parse_mode="Markdown"
    )

    await callback.answer()

# --- ОСТАЛЬНОЕ ---

@dp.callback_query(F.data == "other")
async def other(callback: types.CallbackQuery):

    text = (
        "📦 **Дополнительная информация**\n\n"
        f"👨‍💻 Поддержка: {SUPPORT_USER}\n"
        "📰 Новости: @AuraVPN_News\n"
        "🚀 Версия: 1.0"
    )

    await callback.message.answer(
        text,
        parse_mode="Markdown"
    )

    await callback.answer()

# --- АДМИНКА ---

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    data = callback.data.split("_")

    action = data[1]
    client_id = int(data[2])

    if action == "confirm":

        await bot.send_message(
            client_id,
            f"✅ **Оплата подтверждена!**\n\n"
            f"Напишите в поддержку {SUPPORT_USER} для получения ключа.",
            parse_mode="Markdown"
        )

        await callback.message.edit_text(
            callback.message.text + "\n\n🟢 ОДОБРЕНО",
            parse_mode="Markdown"
        )

    elif action == "decline":

        await bot.send_message(
            client_id,
            f"❌ **Оплата не найдена**\n\n"
            f"Свяжитесь с поддержкой: {SUPPORT_USER}",
            parse_mode="Markdown"
        )

        await callback.message.edit_text(
            callback.message.text + "\n\n🔴 ОТКЛОНЕНО",
            parse_mode="Markdown"
        )

    await callback.answer()

# --- НАЗАД ---

@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "👋 **Добро пожаловать в AuraVPN!**\n\n"
        "Выберите раздел ниже:",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

    await callback.answer()

# --- ЗАПУСК ---

async def main():

    print("AuraVPN BOT STARTED")

    await dp.start_polling(bot)

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("BOT STOPPED")
