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

# Базовые цены на тарифы (за 1 устройство)
BASE_PRICES = {
    "7": 39,
    "30": 99,
    "90": 279,
    "180": 549
}

def main_kb():
    """Главное меню бота (в точности 3 функции)"""
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💳 Купить VPN", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="💰 Заработать с AuraVPN", callback_data="earn"))
    kb.row(types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    return kb.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):
    # Реферальная система при первом переходе
    args = message.text.split()
    user_id = message.from_user.id
    
    if len(args) > 1:
        referrer_id = args[1]
        try:
            referrer_id = int(referrer_id)
            if referrer_id != user_id:
                if referrer_id not in referrals_db:
                    referrals_db[referrer_id] = set()
                
                if user_id not in referrals_db[referrer_id]:
                    referrals_db[referrer_id].add(user_id)
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
    ref_count = len(referrals_db.get(user.id, set()))
    
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


# 2. РАЗДЕЛ: ЗАРАБОТАТЬ (РЕФЕРАЛКА)
@dp.callback_query(F.data == "earn")
async def earn(callback: types.CallbackQuery):
    user = callback.from_user
    bot_info = await bot.get_me()
    
    ref_link = f"https://t.me/{bot_info.username}?start={user.id}"
    ref_count = len(referrals_db.get(user.id, set()))

    text = (
        f"💰 *Партнерская программа AuraVPN*\n\n"
        f"Приглашайте друзей и получайте бонусы на свой баланс!\n\n"
        f"👤 Вы пригласили: *{ref_count}* чел.\n\n"
        f"🔗 *Ваша реферальная ссылка:*\n"
        f"`{ref_link}`\n\n"
        f"_Нажмите на ссылку выше, чтобы скопировать её._"
    )

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()


# 3. РАЗДЕЛ: КУПИТЬ VPN (ШАГ 1: ВЫБОР ТАРИФА)
@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📅 7 дней — 39₽", callback_data="device_7"))
    kb.row(types.InlineKeyboardButton(text="📅 30 дней — 99₽", callback_data="device_30"))
    kb.row(types.InlineKeyboardButton(text="📅 90 дней — 279₽", callback_data="device_90"))
    kb.row(types.InlineKeyboardButton(text="📅 180 дней — 549₽", callback_data="device_180"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    await callback.message.edit_text("💳 Выберите срок действия VPN:", reply_markup=kb.as_markup())
    await callback.answer()


# ШАГ 2: ВЫБОР КОЛИЧЕСТВА УСТРОЙСТВ
@dp.callback_query(F.data.startswith("device_"))
async def choose_devices(callback: types.CallbackQuery):
    days = callback.data.split("_")[1]
    
    kb = InlineKeyboardBuilder()
    # callback_data передает формат: pay_Срок_КоличествоУстройств
    kb.row(types.InlineKeyboardButton(text="📱 1 устройство (Базовая цена)", callback_data=f"pay_{days}_1"))
    kb.row(types.InlineKeyboardButton(text="📱📱 2 устройства (+50% к цене)", callback_data=f"pay_{days}_2"))
    kb.row(types.InlineKeyboardButton(text="💻📱🖥 3 устройства (+100% к цене)", callback_data=f"pay_{days}_3"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Изменить тариф", callback_data="buy"))

    await callback.message.edit_text("📱 Выберите количество устройств для подключения:", reply_markup=kb.as_markup())
    await callback.answer()


# ШАГ 3: ДИНАМИЧЕСКИЙ РАСЧЕТ И ОПЛАТА
@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: types.CallbackQuery):
    _, days, devices = callback.data.split("_")
    devices = int(devices)
    
    # Расчет цены: 1 устр = 100%, 2 устр = 150%, 3 устр = 200% от базовой цены
    base_price = BASE_PRICES[days]
    if devices == 1:
        total_amount = base_price
    elif devices == 2:
        total_amount = int(base_price * 1.5)
    else:
        total_amount = base_price * 2

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{total_amount}"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад к устройствам", callback_data=f"device_{days}"))

    await callback.message.edit_text(
        f"💳 *Оплата VPN*\n\n"
        f"📅 Срок: {days} дней\n"
        f"📱 Устройств: {devices}\n"
        f"💰 Итоговая сумма: *{total_amount}₽*\n\n"
        f"💳 Карта для оплаты:\n`{UMONEY_CARD}`\n\n"
        f"После оплаты нажмите кнопку «Я оплатил».",
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# ШАГ 4: ПРОВЕРКА И ПЕРЕДАЧА АДМИНУ
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
        f"💳 Сумма к проверке: {amount}₽",
        parse_mode="Markdown",
        reply_markup=admin_kb.as_markup()
    )
    await callback.answer()


# ОДОБРЕНИЕ АДМИНИСТРАТОРОМ
@dp.callback_query(F.data.startswith("accept_"))
async def admin_accept(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    try:
        await bot.send_message(
            user_id,
            "✅ *Ваша оплата успешно подтверждена!*\n\n"
            "🔑 *Ваш ключ HappVPN:*\n\n"
            "`https://brandsummerown.online/apx/ppmjdX4AKTwheNf_`\n\n"
            "📲 Как подключить:\n"
            "1️⃣ Откройте HappVPN\n"
            "2️⃣ Нажмите «Импорт подписки»\n"
            "3️⃣ Вставьте ключ\n"
            "4️⃣ Подключитесь\n\n"
            "🚀 VPN успешно активирован.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n🟢 *Статус: Одобрено*",
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.reply(f"❌ Ошибка отправки пользователю: {e}")

    await callback.answer()


# ОТКЛОНЕНИЕ АДМИНИСТРАТОРОМ
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


# КНОПКА ОБЩЕГО НАЗАД (ВОЗВРАТ В ГЛАВНОЕ МЕНЮ)
@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    text = (
        "🏠 **Главное меню**\n\n"
        "👋 Добро пожаловать в AuraVPN\n"
        "🌐 Быстрый VPN без ограничений\n\n"
        "Выберите действие ниже:"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_kb())
    await callback.answer()


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
