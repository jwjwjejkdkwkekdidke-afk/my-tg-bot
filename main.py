import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ ---
TOKEN = (
    os.getenv("MY_BOT_TOKEN") or 
    os.getenv("TELEGRAM_BOT_TOKEN") or 
    os.getenv("TOKEN")
)

UMONEY_CARD = os.getenv("UMONEY_CARD", "2204128123651537")

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8052913358"))
except (ValueError, TypeError):
    ADMIN_ID = 8052913358

if not TOKEN:
    raise ValueError("ОШИБКА: Токен бота не найден в переменных окружения хостинга!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВРЕМЕННАЯ БАЗА ДАННЫХ ---
referrals_db = {}

def get_user_data(user_id: int):
    if user_id not in referrals_db:
        referrals_db[user_id] = {"referrals": set(), "balance": 0.0}
    return referrals_db[user_id]

# --- УЗНАТЬ ID КАРТИНКИ (ВРЕМЕННО) ---
@dp.message(F.photo)
async def get_photo_id(message: types.Message):
    photo_id = message.photo[-1].file_id
    await message.answer(f"Вот file_id этой картинки:\n\n{photo_id}")

# --- КЛАВИАТУРЫ ---
def main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🛡 Управление VPN", callback_data="management"))
    kb.row(
        types.InlineKeyboardButton(text="👥 Реферальная программа", callback_data="referral"),
        types.InlineKeyboardButton(text="💬 Поддержка", callback_data="support")
    )
    kb.row(types.InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"))
    return kb.as_markup()

# --- ОБРАБОТЧИК /START ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    args = message.text.split()
    user_id = message.from_user.id
    get_user_data(user_id)
    
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
                            "🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass

    text = (
        "✨ **Добро пожаловать в AuraVPN**\n\n"
        "💬 *Надёжный VPN без логов, без ограничений по скорости и трафику.*\n\n"
        "⬇️ Выберите раздел в меню ниже:"
    )
    
    await message.answer(
        text=text,
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

# --- 1. УПРАВЛЕНИЕ VPN ---
@dp.callback_query(F.data == "management")
async def management_menu(callback: types.CallbackQuery):
    text = (
        "🛡 **Управление VPN**\n\n"
        "Здесь вы можете проверить статус вашей подписки, посмотреть активные устройства или продлить доступ.\n\n"
        "📅 **Статус:** Не активна\n"
        "📱 **Устройств подключено:** 0 / 1"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📱 Устройства", callback_data="devices"))
    kb.row(types.InlineKeyboardButton(text="📅 Продлить подписку", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back"))

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "devices")
async def devices_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="➕ Подключить новое устройство", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="management"))

    await callback.message.edit_text(
        text="📱 **Ваши устройства**\n\nУ вас пока нет активных подключений.",
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# --- 2. РЕФЕРАЛЬНАЯ ПРОГРАММА ---
@dp.callback_query(F.data == "referral")
async def referral_menu(callback: types.CallbackQuery):
    user = callback.from_user
    bot_info = await bot.get_me()
    user_data = get_user_data(user.id)
    
    ref_count = len(user_data["referrals"])
    ref_balance = user_data["balance"]
    ref_link = f"https://t.me/{bot_info.username}?start={user.id}"

    text = (
        "👥 **Реферальная программа**\n\n"
        f"🔗 **Ваша ссылка:**\n`{ref_link}`\n\n"
        f"👥 Приглашено: *{ref_count}* чел.\n"
        f"👛 Заработано: *{ref_balance} ₽*\n\n"
        "Вы получаете **20%** с каждой покупки вашего реферала."
    )

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💸 Вывести средства", callback_data="withdraw"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back"))

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def withdraw_funds(callback: types.CallbackQuery):
    await callback.answer("⚠️ Минимальная сумма для вывода: 150 ₽", show_alert=True)

# --- 3. ПОДДЕРЖКА ---
@dp.callback_query(F.data == "support")
async def support_menu(callback: types.CallbackQuery):
    text = (
        "✍️ **Напишите свой вопрос для создания тикета.**\n\n"
        "Чтобы мы могли быстрее помочь, сразу отправляйте:\n"
        "1. Описание проблемы.\n"
        "2. Скриншот ошибки / экрана при необходимости.\n"
        "3. Когда возникла проблема.\n\n"
        "Пожалуйста, **НЕ** нужно писать просто:\n"
        "«привет», «здравствуйте», «не работает» и ждать ответа.\n\n"
        "❤️ Так мы сможем быстрее проверить информацию и решить проблему."
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back"))

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# --- 4. ИНФОРМАЦИЯ ---
@dp.callback_query(F.data == "info")
async def info_menu(callback: types.CallbackQuery):
    text = (
        "ℹ️ **Информация и правила AuraVPN**\n\n"
        "🔒 **Безопасность и конфиденциальность:**\n"
        "Мы не собираем и не храним логи вашей сетевой активности (No-Logs Policy).\n\n"
        "⚡ **Почему это не обман:**\n"
        "Сервис работает на базе современных высокоскоростных протоколов."
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back"))

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# --- ПОКУПКА / ТАРИФЫ ---
@dp.callback_query(F.data == "buy")
async def buy_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📅 7 дней — 39₽", callback_data="pay_7"))
    kb.row(types.InlineKeyboardButton(text="📅 30 дней — 99₽", callback_data="pay_30"))
    kb.row(types.InlineKeyboardButton(text="📅 90 дней — 279₽", callback_data="pay_90"))
    kb.row(types.InlineKeyboardButton(text="📅 180 дней — 549₽", callback_data="pay_180"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="management"))

    await callback.message.edit_text(
        text="💳 **Выберите срок подписки:**", 
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def payment_process(callback: types.CallbackQuery):
    days = callback.data.split("_")[1]
    prices = {"7": "39", "30": "99", "90": "279", "180": "549"}
    amount = prices.get(days, "99")

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{amount}"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="buy"))

    text = (
        f"💳 **Оплата VPN**\n\n"
        f"Срок: {days} дней\n"
        f"Сумма к оплате: *{amount}₽*\n\n"
        f"Карта для перевода:\n`{UMONEY_CARD}`\n\n"
        f"После оплаты нажмите кнопку ниже."
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    
    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 **Новая заявка на оплату!**\n\n"
                f"👤 Пользователь: @{callback.from_user.username} (ID: `{callback.from_user.id}`)\n"
                f"💰 Сумма: {amount}₽",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await callback.answer(
        "✅ Заявка принята! Ожидайте проверки администратором.", 
        show_alert=True
    )

# --- ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ---
@dp.callback_query(F.data == "back")
async def back_to_main(callback: types.CallbackQuery):
    text = (
        "✨ **Добро пожаловать в AuraVPN**\n\n"
        "💬 *Надёжный VPN без логов, без ограничений по скорости и трафику.*\n\n"
        "⬇️ Выберите раздел в меню ниже:"
    )
    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=main_kb()
    )
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    print("BOT STARTED SUCCESSFULLY")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
