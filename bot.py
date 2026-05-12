


WEBAPP_URL = "https://fitness-miniapp.onrender.com/"
import pytz
import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from threading import Thread

from flask import Flask, render_template
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

TOKEN = "8733448156:AAFkVO59emlRIazwOVXGewwK0UGeEb5SAos"

ADMIN_IDS = [
    601663687
]

WORK_START = 10
WORK_END = 21
DAYS_AHEAD = 7

logging.basicConfig(level=logging.INFO,
        reply_markup=keyboard
    )

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
router = Router()
dp.include_router(router)

conn = sqlite3.connect("bookings.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_date TEXT,
    booking_time TEXT,
    user_id INTEGER,
    username TEXT,
    full_name TEXT,
    comment TEXT
)
""")

conn.commit()

app = Flask(__name__)


class BookingState(StatesGroup):
    waiting_comment = State()


def generate_slots():
    return [f"{hour}:00" for hour in range(WORK_START, WORK_END)]


def is_past_slot(date_str, slot):
    tz = pytz.timezone("Europe/Kiev")

    now = datetime.now(tz)

    slot_datetime = tz.localize(
        datetime.strptime(
            f"{date_str} {slot}",
            "%Y-%m-%d %H:%M"
        )
    )

    return slot_datetime <= now


def cleanup_old_bookings():
    now = datetime.now()

    cursor.execute(
        "SELECT id, booking_date, booking_time FROM bookings"
    )

    rows = cursor.fetchall()

    for booking_id, date_str, time_str in rows:
        slot_dt = datetime.strptime(
            f"{date_str} {time_str}",
            "%Y-%m-%d %H:%M"
        )

        if slot_dt < now:
            cursor.execute(
                "DELETE FROM bookings WHERE id = ?",
                (booking_id,)
            )

    conn.commit()


def get_free_slots(date_str):
    cleanup_old_bookings()

    cursor.execute(
        "SELECT booking_time FROM bookings WHERE booking_date = ?",
        (date_str,)
    )

    booked = [row[0] for row in cursor.fetchall()]

    result = []

    for slot in generate_slots():
        # ПРОШЕДШЕЕ ВРЕМЯ АВТОМАТИЧЕСКИ СКРЫВАЕТСЯ
        if slot not in booked and not is_past_slot(date_str, slot):
            result.append(slot)

    return result


def create_dates_keyboard():
    builder = InlineKeyboardBuilder()

    for i in range(DAYS_AHEAD):
        date = datetime.now() + timedelta(days=i)

        builder.button(
            text=f"🏋️ {date.strftime('%d.%m')}",
            callback_data=f"date|{date.strftime('%Y-%m-%d')}"
        )

    builder.adjust(2)

    return builder.as_markup()


def create_slots_keyboard(date_str):
    builder = InlineKeyboardBuilder()

    free_slots = get_free_slots(date_str)

    if not free_slots:
        builder.button(
            text="❌ Нет свободных тренировок",
            callback_data="none"
        )
    else:
        for slot in free_slots:
            builder.button(
                text=f"🔥 {slot}",
                callback_data=f"book|{date_str}|{slot}"
            )

    builder.button(
        text="⬅️ Назад",
        callback_data="back_dates"
    )

    builder.adjust(2)

    return builder.as_markup()



@router.message(Command("start"))
async def start(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ Записатися",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Мої записи",
                    callback_data="my_bookings"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Підтримка",
                    url="https://t.me/"
                )
            ]
        ]
    )

    await bot.send_photo(
        chat_id=message.chat.id,
        photo="https://images.unsplash.com/photo-1518611012118-696072aa579a?q=80&w=1200",
caption=(
    "✨ <b>Онлайн запис на тренування</b>\\n\\n"
    "🤍 Персональні тренування\\n"
    "🧘 Stretching • Wellness • Fitness\\n\\n"
    "Оберіть потрібну дію нижче ✨"
),
        reply_markup=keyboard,
        parse_mode="HTML"
    )



@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):

    cursor.execute(
        '''
        SELECT booking_date, booking_time
        FROM bookings
        WHERE user_id = ?
        ORDER BY booking_date, booking_time
        ''',
        (callback.from_user.id,)
    )

    rows = cursor.fetchall()

    if not rows:
        await callback.message.answer(
            "🤍 У вас поки немає активних записів"
        )
        return

text = "📅 <b>Ваші записи</b>\\n\\n"

for row in rows:
    text += (
        f"✨ {row[0]} • {row[1]}\\n"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML"
    )

@router.message(Command("start"))
async def start(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ Відкрити запис",
                    web_app=WebAppInfo(
                        url="https://fitness-miniapp.onrender.com/"
                    )
                )
            ]
        ]
    )

    await message.answer(
        "✨ Оберіть формат запису",
        reply_markup=keyboard
    )
    
@router.message(Command("start"))
async def start(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ Відкрити запис",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    )
                )
            ]
        ]
    )

    await message.answer(
        "✨ <b>Онлайн запис на тренування</b>\\n\\n"
        "🤍 Персональні тренування\\n"
        "🧘 Stretching • Wellness • Fitness\\n\\n"
        "Оберіть потрібну дію нижче ✨",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("date|"))
async def select_date(callback: CallbackQuery):
    _, date_str = callback.data.split("|")

    await callback.message.edit_text(
        f"🏋️ <b>{date_str}</b>\n\n"
        f"Оберіть час тренування:",
        reply_markup=create_slots_keyboard(date_str)
    )


@router.callback_query(F.data.startswith("book|"))
async def booking(callback: CallbackQuery, state: FSMContext):
    _, date_str, slot = callback.data.split("|")

    if is_past_slot(date_str, slot):
        await callback.answer(
            "Цей час вже пройшов",
            show_alert=True
        )
        return

    await state.update_data(
        booking_date=date_str,
        booking_time=slot
    )

    await state.set_state(BookingState.waiting_comment)

    await callback.message.edit_text(
        f"✍️ Напишіть коментар, побажання до запису\n\n"
        f"Например:\n"
        f"• Хочу тренування на ноги\n"
        f"• Перший раз у залі\n"
        f"• Групове заняття\n\n"
        f"Або відправте '-' немає побажань"
    )


@router.message(BookingState.waiting_comment)
async def save_booking(message: Message, state: FSMContext):
    data = await state.get_data()

    date_str = data["booking_date"]
    slot = data["booking_time"]

    comment = message.text

    user_id = message.from_user.id
    username = message.from_user.username or "no_username"
    full_name = message.from_user.full_name

    cursor.execute(
        """
        SELECT * FROM bookings
        WHERE booking_date = ?
        AND booking_time = ?
        """,
        (date_str, slot)
    )

    if cursor.fetchone():
        await message.answer("❌ Цей час вже зайнято")
        await state.clear()
        return

    cursor.execute(
        """
        INSERT INTO bookings
        (
            booking_date,
            booking_time,
            user_id,
            username,
            full_name,
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            date_str,
            slot,
            user_id,
            username,
            full_name,
            comment
        )
    )

    conn.commit()

    booking_id = cursor.lastrowid

    await message.answer(
        f"✅ <b>Тренування заброньоване</b>\n\n"
        f"📅 {date_str}\n"
        f"⏰ {slot}\n"
        f"💬 {comment}\n\n"
        f"Скасування:\n/cancel_{booking_id}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🔥 <b>✨ Новий запис</b>\n\n"
                f"👤 {full_name}\n"
                f"📅 {date_str}\n"
                f"⏰ {slot}\n"
                f"💬 {comment}\n"
                f"📱 @{username}"
            )
        except:
            pass

    await state.clear()


@router.message(F.text.startswith("/cancel_"))
async def cancel_booking(message: Message):
    try:
        booking_id = int(
            message.text.replace("/cancel_", "")
        )
    except:
        return

    cursor.execute(
        "DELETE FROM bookings WHERE id = ?",
        (booking_id,)
    )

    conn.commit()

    await message.answer("❌ ❌ Запис скасовано")


@app.route("/")
def admin_panel():
    cleanup_old_bookings()

    cursor.execute(
        """
        SELECT
            booking_date,
            booking_time,
            full_name,
            username,
            comment
        FROM bookings
        ORDER BY booking_date, booking_time
        """
    )

    rows = cursor.fetchall()

    return render_template(
        "index.html",
        bookings=rows
    )


def run_flask():
    app.run(host="0.0.0.0", port=5000)


async def main():
    Thread(target=run_flask).start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
