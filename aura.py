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

# Прямая ссылка на картинку-баннер личного кабинета
# Ты можешь загрузить свою картинку в любой открытый фотохостинг или телеграм-канал и вставить сюда ссылку
BANNER_URL = "https://raw.githubusercontent.com/aiogram/aiogram/dev/assets/logo.png"


def get_profile_text(user_id: int, user_name: str) -> str:
    """Функция генерации красивого текста профиля в одном стиле"""
    ref_count = len(referrals_db.get(user_id, set()))
    return (
        f"👤 **Профиль {user_name}:** 💯\n\n"
        f"➖ **ID:** `{user_id}`\n"
        f"➖ **Баланс:** 0 ₽ RUB\n"
        f"➖ **К-во подписок:** 0\n"
        f"➖ **Приглашено друзей:** {ref_count}"
    )


def profile_kb():
    """Вертикальное меню кнопок личного кабинета"""
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="➕ Купить новую подписку", callback_data="buy"))
    kb.row(types.InlineKeyboardButton(text="🎁 Подарить другу", callback_data="gift_friend"))
    kb.row(types.InlineKeyboardButton(text="💰 Заработать с AuraVPN", callback_data="earn"))
    kb.row(types.InlineKeyboardButton(text="💬 О сервисе", callback_data="about"))
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

    # Теперь сразу после /start бот присылает ЛИЧНЫЙ КАБИНЕТ с баннером
    await message.answer_photo(
        photo=BANNER_URL,
        caption=get_profile_text(user_id, message.from_user.first_name),
        parse_mode="Markdown",
        reply_markup=profile_kb()
    )


@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    """Возврат в меню профиля из других вкладок"""
    user = callback.from_user
    
    # Если мы уже находимся в сообщении с фото, просто обновляем его текст и кнопки
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=get_profile_text(user.id, user.first_name),
            parse_mode="Markdown",
            reply_markup=profile_kb()
        )
    else:
        # Если вдруг фото не было, удаляем старое сообщение и шлем заново профиль
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=BANNER_URL,
            caption=get_profile_text(user.id, user.first_name),
            parse_mode="Markdown",
            reply_markup=profile_kb()
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

    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=kb.as_markup())
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

    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()


# Заглушка для подарка
@dp.callback_query(F.data == "gift_friend")
async def gift_friend(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile"))
    
    await callback.message.edit_caption(
        caption="🎁 Функция отправки подарка другу находится в разработке.", 
        reply_markup=kb.as_markup()
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
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile"))

    # Так как это финансовое меню, мы удаляем медиа-карточку профиля, переходя на чистый текст оплаты
    await callback.message.delete()
    await callback.message.answer("💳 Выберите тариф VPN:", reply_markup=kb.as_markup())
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


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
