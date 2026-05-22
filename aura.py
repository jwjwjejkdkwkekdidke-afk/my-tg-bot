import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# УКАЖИ СВОИ ДАННЫЕ ЗДЕСЬ:
TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН"
UMONEY_CARD = "0000 0000 0000 0000"
ADMIN_ID = 123456789  # Вставь свой Telegram ID цифрами

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных для рефералов
referrals_db = {}


def get_user_data(user_id: int):
    """Инициализация данных пользователя в мини-БД"""
    if user_id not in referrals_db:
        referrals_db[user_id] = {"referrals": set(), "balance": 0.0}
    return referrals_db[user_id]


def main_kb():
    """Главное инлайн-меню (строго 3 функции)"""
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


# 3. РАЗДЕЛ: КУПИТЬ VPN (ТАРИФЫ)
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


# ВЫБОР КОЛИЧЕСТВА УСТРОЙСТВ
@dp.callback_query(F.data.startswith("device_"))
async def choose_devices(callback: types.CallbackQuery):
    days = callback.data.split("_")[1]
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📱 1 устройство (Базовая цена)", callback_data=f"pay_{days}_1"))
    kb.row(types.InlineKeyboardButton(text="📱📱 2 устройства (+50%)", callback_data=f"pay_{days}_2"))
    kb.row(types.InlineKeyboardButton(text="💻📱🖥 3 устройства (+100%)", callback_data=f"pay_{days}_3"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Изменить тариф", callback_data="buy"))

    await callback.message.edit_text("📱 Выберите количество устройств для подключения:", reply_markup=kb.as_markup())
    await callback.answer()


# СТРАНИЦА ОПЛАТЫ С ДИНАМИЧЕСКИМ РАСЧЕТОМ
@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    days = data_parts[1]
    devices = int(data_parts[2])
    
    base_prices = {"7": 39, "30": 99, "90": 279, "180": 549}
    base_price = base_prices[days]
    
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


# ПРОВЕРКА ОПЛАТЫ АДМИНОМ
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


# КНОПКА ВОЗВРАТА В ГЛАВНОЕ МЕНЮ
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
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
