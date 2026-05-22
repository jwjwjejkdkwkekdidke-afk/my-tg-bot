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
    kb.row(types.InlineKeyboardButton(text="💳 Купить VPN", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="⚡️ Подключиться", callback_data="connect"))
    kb.row(types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    return kb.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):
    text = (
        "👋 Добро пожаловать в AuraVPN\n\n"
        "🌐 Быстрый VPN без ограничений\n"
        "📍 Стабильные сервера\n\n"
        "Выберите действие ниже."
    )
    await message.answer(text, reply_markup=main_kb())


@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user = callback.from_user
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    profile_text = (
        f"👤 *Ваш профиль:*\n\n"
        f"📝 Имя: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📅 Подписка: Не активна"
    )
    await callback.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📅 7 дней — 39₽", callback_data="pay_39"))
    kb.row(types.InlineKeyboardButton(text="📅 30 дней — 99₽", callback_data="pay_99"))
    kb.row(types.InlineKeyboardButton(text="📅 90 дней — 279₽", callback_data="pay_279"))
    kb.row(types.InlineKeyboardButton(text="📅 180 дней — 549₽", callback_data="pay_549"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    await callback.message.edit_text("💳 Выберите тариф VPN:", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{amount}"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="buy"))

    await callback.message.edit_text(
        f"💳 Оплата VPN\n\nСумма: {amount}₽\n\n💳 Карта для оплаты:\n{UMONEY_CARD}\n\nПосле оплаты нажмите кнопку «Я оплатил».",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("check_"))
async def check(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    user = callback.from_user

    await callback.message.edit_text(
        "✅ Оплата отправлена на проверку.\n\n⏳ Ожидайте ваш VPN код.\nКлюч придёт автоматически после проверки оплаты."
    )

    admin_kb = InlineKeyboardBuilder()
    admin_kb.row(
        types.InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{user.id}"),
        types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{user.id}")
    )

    await bot.send_message(
        ADMIN_ID,
        f"💸 *Новая заявка на VPN*\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"💳 Сумма: {amount}₽",
        parse_mode="Markdown",
        reply_markup=admin_kb.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("accept_"))
async def admin_accept(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    try:
        await bot.send_message(
            user_id,
            "✅ *Ваша оплата успешно подтверждена!*\n\n"
            "🔑 Ваш ключ для подключения: `vless://your_key_here` \n\n"
            "📲 Скопируйте ключ и вставьте его в приложение HappVPN.",
            parse_mode="Markdown"
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n🟢 *Статус: Одобрено*",
            parse_mode="Markdown"
        )

    except Exception as e:
        await callback.message.reply(f"❌ Ошибка отправки пользователю: {e}")

    await callback.answer()


@dp.callback_query(F.data.startswith("decline_"))
async def admin_decline(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    try:
        await bot.send_message(
            user_id,
            "❌ *Оплата не была подтверждена.*\n\n"
            "Если вы действительно оплатили, пожалуйста, свяжитесь с администратором.",
            parse_mode="Markdown"
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n🔴 *Статус: Отклонено*",
            parse_mode="Markdown"
        )

    except Exception as e:
        await callback.message.reply(f"❌ Ошибка отправки пользователю: {e}")

    await callback.answer()


@dp.callback_query(F.data == "connect")
async def connect(callback: types.CallbackQuery):
    await callback.message.answer("📲 Скачайте HappVPN и вставьте полученный ключ.")
    await callback.answer()


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=main_kb())
    await callback.answer()


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
