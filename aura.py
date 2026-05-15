import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# --- СЕКРЕТНЫЕ ДАННЫЕ ИЗ ENV ---
TOKEN = os.getenv("BOT_TOKEN")
UMONEY_CARD = os.getenv("UMONEY_CARD")
SUPPORT_USER = os.getenv("SUPPORT_USER")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---

def main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"))
    kb.row(types.InlineKeyboardButton(text="⚡️ Подключиться", callback_data="connect"))
    kb.row(types.InlineKeyboardButton(text="📦 Остальное", callback_data="other"))
    return kb.as_markup()

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start"))
async def start(message: types.Message):
    text = (
        "Привет 👋 **Это AuraVPN** — твой надежный сервис ✨\n\n"
        "🌐 YouTube, Instagram, Discord без блокировок.\n"
        "📍 Локации: 🇸🇪 🇨🇭 🇪🇸 🇩🇪 🇦🇹 🇳🇱 🇬🇪\n\n"
        "Включай VPN и забудь про ограничения 🙌"
    )
    await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

# --- ЛОГИКА ОПЛАТЫ ---

@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🗓 1 месяц — 300₽", callback_data="p_300"))
    kb.row(types.InlineKeyboardButton(text="🗓 3 месяца — 800₽", callback_data="p_800"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    await callback.message.edit_text(
        "💳 **Выберите тариф AuraVPN:**",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("p_"))
async def pay(callback: types.CallbackQuery):
    summ = callback.data.split("_")[1]

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{summ}"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="buy"))

    await callback.message.edit_text(
        f"💳 **Оплата: {summ}₽**\n"
        f"ЮMoney/Карта: `{UMONEY_CARD}`\n\n"
        "Переведите сумму и нажмите кнопку ниже для проверки.",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("check_"))
async def check(callback: types.CallbackQuery):
    summ = callback.data.split("_")[1]
    user = callback.from_user

    await callback.answer("Заявка отправлена!", show_alert=True)

    await callback.message.answer(
        f"⏳ **Заявка принята!**\n"
        f"Скиньте чек сюда: {SUPPORT_USER}"
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
        f"💰 **НОВАЯ ОПЛАТА!**\n\n"
        f"Юзер: {user.full_name} (@{user.username})\n"
        f"ID: `{user.id}`\n"
        f"Сумма: {summ}₽",
        reply_markup=admin_kb.as_markup()
    )

# --- ЛОГИКА ДРУГИХ КНОПОК ---

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    await callback.answer()

    text = (
        f"👤 **Ваш профиль AuraVPN**\n\n"
        f"🆔 ID: `{callback.from_user.id}`\n"
        f"📊 Статус: **Не активен**\n"
        f"⏳ Срок действия: —"
    )

    await callback.message.answer(text, parse_mode="Markdown")

@dp.callback_query(F.data == "connect")
async def connect(callback: types.CallbackQuery):
    await callback.answer()

    text = (
        "⚡️ **Как подключиться к AuraVPN?**\n\n"
        "1️⃣ Скачайте приложение:\n"
        "— iOS / Android: **HappVpn**\n\n"
        "2️⃣ После покупки вы получите персональную ссылку (ключ).\n"
        "3️⃣ Вставьте её в приложение и нажмите 'Подключить'."
    )

    await callback.message.answer(text, parse_mode="Markdown")

@dp.callback_query(F.data == "other")
async def other(callback: types.CallbackQuery):
    await callback.answer()

    text = (
        "📦 **Дополнительная информация**\n\n"
        f"— Техподдержка: {SUPPORT_USER}\n"
        "— Новости сервиса: @AuraVPN_News\n"
        "— Версия бота: 1.0"
    )

    await callback.message.answer(text, parse_mode="Markdown")

# --- АДМИН ПАНЕЛЬ ---

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    data = callback.data.split("_")
    action, client_id = data[1], int(data[2])

    if action == "confirm":
        await bot.send_message(
            client_id,
            f"✅ **Оплата подтверждена!**\n"
            f"Ваш доступ активирован.\n"
            f"Напишите в поддержку {SUPPORT_USER} за ключом для **HappVpn**."
        )

        await callback.message.edit_text(
            callback.message.text + "\n\n🟢 **ОДОБРЕНО**"
        )

    elif action == "decline":
        await bot.send_message(
            client_id,
            f"❌ **Оплата не найдена.**\n"
            f"Свяжитесь с поддержкой: {SUPPORT_USER}"
        )

        await callback.message.edit_text(
            callback.message.text + "\n\n🔴 **ОТКЛОНЕНО**"
        )

    await callback.answer()

@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "👋 **Добро пожаловать в AuraVPN!**\n"
        "Выбирайте раздел в меню ниже:",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

async def main():
    print("Бот AuraVPN успешно запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
