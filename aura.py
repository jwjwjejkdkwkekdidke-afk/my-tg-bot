import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN", "ТВОЙ_ТОКЕН")
UMONEY_CARD = os.getenv("UMONEY_CARD", "0000 0000 0000 0000")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных для рефералов
referrals_db = {}


def main_kb():
    """Главное меню бота"""
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💳 Купить VPN", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="⚡️ Подключиться", callback_data="connect"))
    kb.row(types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    return kb.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):
    # Логика реферальной системы при переходе по ссылке
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
                            f"🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass

    text = (
        "👋 Добро пожаловать в AuraVPN\n\n"
        "🌐 Быстрый VPN без ограничений\n"
        "📍 Стабильные сервера\n\n"
        "Выберите действие ниже:"
    )
    await message.answer(text, reply_markup=main_kb())


# Новый профиль с баннером и кнопками (как на скриншоте 2)
@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user = callback.from_user
    ref_count = len(referrals_db.get(user.id, set()))
    
    # Удаляем старое текстовое сообщение, чтобы красиво отправить баннер
    await callback.message.delete()

    profile_text = (
        f"👤 **Профиль:** 💯\n\n"
        f"➖ **ID:** `{user.id}`\n"
        f"➖ **Баланс:** 0 ₽ RUB\n"
        f"➖ **К-во подписок:** 0\n"
        f"➖ **Приглашено друзей:** {ref_count}\n\n"
        f"╭───────────────────────────╮\n"
        f"│ 🔧 _Нажмите кнопку ➕ Добавить новую подписку, чтобы_ │\n"
        f"│ _настроить VPN-подключение_                          │\n"
        f"╰───────────────────────────╯"
    )

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="➕ Купить новую подписку", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="🎁 Подарить другу", callback_data="gift_friend"))
    kb.row(types.InlineKeyboardButton(text="💰 Заработать с AuraVPN", callback_data="earn"))
    kb.row(types.InlineKeyboardButton(text="💬 О сервисе", callback_data="about"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu"))

    try:
        photo = FSInputFile("banner.jpg")
        await callback.message.answer_photo(
            photo=photo, 
            caption=profile_text, 
            parse_mode="Markdown", 
            reply_markup=kb.as_markup()
        )
    except Exception:
        # Если баннер забыли положить в папку с ботом
        await callback.message.answer(
            f"🖼️ (Добавьте файл banner.jpg в папку)\n\n{profile_text}", 
            parse_mode="Markdown", 
            reply_markup=kb.as_markup()
        )
    
    await callback.answer()


# Раздел: Заработать (Реферальная ссылка)
@dp.callback_query(F.data == "earn")
async def earn(callback: types.CallbackQuery):
    user = callback.from_user
    bot_info = await bot.get_me()
    
    ref_link = f"https://t.me/{bot_info.username}?start={user.id}"
    ref_count = len(referrals_db.get(user.id, set()))

    text = (
        f"💰 *Партнерская программа AuraVPN*\n\n"
        f"Приглашайте друзей и получайте бонусы на свой баланс для оплаты подписки!\n\n"
        f"👤 Вы пригласили: *{ref_count}* чел.\n\n"
        f"🔗 *Ваша реферальная ссылка:*\n"
        f"`{ref_link}`\n\n"
        f"_Нажмите на ссылку, чтобы скопировать её._"
    )

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile"))

    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=kb.as_markup())
    else:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb.as_markup())
    
    await callback.answer()


# Раздел: О сервисе
@dp.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery):
    text = (
        "💬 *О сервисе AuraVPN*\n\n"
        "🚀 **AuraVPN** — это надежный и высокоскоростной VPN-сервис, созданный для вашей безопасности в сети.\n\n"
        "🔒 Мы используем современные протоколы шифрования, которые гарантируют защиту личных данных, "
        "обход любых блокировок и стабильное подключение без просадки скорости.\n\n"
        "🌍 Наши преимущества:\n"
        "• Высокая скорость до 1 Гбит/с\n"
        "• Нет логов и отслеживания трафика\n"
        "• Простая настройка в пару кликов"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile"))

    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=kb.as_markup())
    else:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb.as_markup())
    
    await callback.answer()


# Заглушка для подарка
@dp.callback_query(F.data == "gift_friend")
async def gift_friend(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile"))
    
    if callback.message.photo:
        await callback.message.edit_caption(caption="🎁 Функция отправки подарка другу находится в разработке.", reply_markup=kb.as_markup())
    else:
        await callback.message.edit_text("🎁 Функция отправки подарка другу находится в разработке.", reply_markup=kb.as_markup())
    await callback.answer()


# Кнопка возврата из профиля (с картинкой) обратно в главное меню
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    text = (
        "👋 Добро пожаловать в AuraVPN\n\n"
        "🌐 Быстрый VPN без ограничений\n"
        "📍 Стабильные сервера\n\n"
        "Выберите действие ниже:"
    )
    await callback.message.answer(text, reply_markup=main_kb())
    await callback.answer()


# Кнопка «Назад» для обычных текстовых окон оплаты
@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Добро пожаловать в AuraVPN\n\nВыберите действие ниже:", 
        reply_markup=main_kb()
    )
    await callback.answer()


# Покупка VPN (Тарифы)
@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📅 7 дней — 39₽", callback_data="pay_39"))
    kb.row(types.InlineKeyboardButton(text="📅 30 дней — 99₽", callback_data="pay_99"))
    kb.row(types.InlineKeyboardButton(text="📅 90 дней — 279₽", callback_data="pay_279"))
    kb.row(types.InlineKeyboardButton(text="📅 180 дней — 549₽", callback_data="pay_549"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))

    # Если перешли из профиля, где была картинка — удаляем её, чтобы открыть текстовое меню
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer("💳 Выберите тариф VPN:", reply_markup=kb.as_markup())
    else:
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
            "🔑 *Ваш ключ HappVPN:*\n\n"
            "`https://brandsummerown.online/apx/ppmjdX4AKTwheNf_`\n\n"
            "📲 Как подключить:\n"
            "1️⃣ Откройте HappVPN\n"
            "2️⃣ Нажмите «Импорт подписки»\n"
            "3️⃣ Вставьте ключ\n"
            "4️⃣ Подключитесь к серверу\n\n"
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


@dp.callback_query(F.data == "connect")
async def connect(callback: types.CallbackQuery):
    await callback.message.answer("📲 Скачайте HappVPN и вставьте полученный ключ.")
    await callback.answer()


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
