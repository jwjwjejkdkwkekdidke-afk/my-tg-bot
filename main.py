import os
import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН_БОТА")

ADMIN_ID = 8052913358

DB_FILE = "auravpn.db"


# =========================
# ЛОГИ
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# =========================
# БАЗА ДАННЫХ
# =========================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()


def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM banned_users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def ban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


# =========================
# СОЗДАНИЕ БОТА
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# КЛАВИАТУРА АДМИНИСТРАТОРА
# =========================

def admin_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Принять",
        callback_data=f"accept:{user_id}"
    )

    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject:{user_id}"
    )

    builder.adjust(2)

    return builder.as_markup()


# =========================
# /START
# =========================

@dp.message(Command("start"))
async def start_handler(message: types.Message):

    user_id = message.from_user.id

    # Проверяем блокировку
    if is_banned(user_id):
        await message.answer(
            "❌ Вы заблокированы и не можете пользоваться этим ботом."
        )
        return

    username = message.from_user.username
    first_name = message.from_user.first_name or "Без имени"

    username_text = (
        f"@{username}"
        if username
        else "без username"
    )

    # Сообщение пользователю
    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Ваша заявка отправлена администратору.\n"
        "Ожидайте решения."
    )

    # Сообщение администратору
    admin_text = (
        "📥 НОВАЯ ЗАЯВКА\n\n"
        f"👤 Имя: {first_name}\n"
        f"🔗 Username: {username_text}\n"
        f"🆔 ID: {user_id}\n\n"
        "Выберите действие:"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=admin_keyboard(user_id)
        )
    except Exception as e:
        logging.error(
            f"Ошибка отправки заявки администратору: {e}"
        )


# =========================
# ОБЫЧНЫЕ СООБЩЕНИЯ
# =========================

@dp.message()
async def message_handler(message: types.Message):

    user_id = message.from_user.id

    # Заблокированные пользователи ничего не могут делать
    if is_banned(user_id):
        await message.answer(
            "❌ Вы заблокированы и не можете пользоваться этим ботом."
        )
        return

    # Если пишет администратор
    if user_id == ADMIN_ID:
        return

    username = message.from_user.username
    first_name = message.from_user.first_name or "Без имени"

    username_text = (
        f"@{username}"
        if username
        else "без username"
    )

    # Текст сообщения пользователя
    if message.text:
        user_message = message.text
    else:
        user_message = "Пользователь отправил сообщение другого типа."

    # Отправляем сообщение администратору
    admin_text = (
        "📩 НОВОЕ СООБЩЕНИЕ\n\n"
        f"👤 Имя: {first_name}\n"
        f"🔗 Username: {username_text}\n"
        f"🆔 ID: {user_id}\n\n"
        f"💬 Сообщение:\n{user_message}\n\n"
        "Выберите действие:"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=admin_keyboard(user_id)
        )

        await message.answer(
            "✅ Сообщение отправлено администратору.\n"
            "Ожидайте ответа."
        )

    except Exception as e:
        logging.error(
            f"Ошибка обработки сообщения: {e}"
        )


# =========================
# КНОПКА «ПРИНЯТЬ»
# =========================

@dp.callback_query(F.data.startswith("accept:"))
async def accept_handler(callback: types.CallbackQuery):

    # Только администратор может нажимать кнопки
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    try:
        user_id = int(
            callback.data.split(":")[1]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Ошибка данных.",
            show_alert=True
        )
        return

    # Уведомляем пользователя
    try:
        await bot.send_message(
            user_id,
            "✅ Ваша заявка принята!"
        )
    except Exception as e:
        logging.error(
            f"Не удалось отправить сообщение пользователю "
            f"{user_id}: {e}"
        )

    # Убираем кнопки у администратора
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await callback.answer("Заявка принята ✅")


# =========================
# КНОПКА «ОТКЛОНИТЬ»
# =========================

@dp.callback_query(F.data.startswith("reject:"))
async def reject_handler(callback: types.CallbackQuery):

    # Только администратор
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    try:
        user_id = int(
            callback.data.split(":")[1]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Ошибка данных.",
            show_alert=True
        )
        return

    # Добавляем пользователя в блок-лист
    ban_user(user_id)

    # Уведомляем пользователя
    try:
        await bot.send_message(
            user_id,
            "❌ Ваша заявка была отклонена.\n"
            "Вы больше не можете пользоваться этим ботом."
        )
    except Exception as e:
        logging.error(
            f"Не удалось уведомить пользователя "
            f"{user_id}: {e}"
        )

    # Убираем кнопки
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    # Сообщение администратору
    try:
        await callback.message.edit_text(
            callback.message.text
            + "\n\n❌ ОТКЛОНЕНО — пользователь ЗАБЛОКИРОВАН"
        )
    except Exception:
        pass

    await callback.answer(
        "Пользователь заблокирован ❌"
    )


# =========================
# ЗАПУСК
# =========================

async def main():

    init_db()

    logging.info("Бот запускается...")

    try:
        await bot.delete_webhook(
            drop_pending_updates=True
        )
    except Exception as e:
        logging.warning(
            f"Не удалось удалить webhook: {e}"
        )

    logging.info("Бот запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен.")
