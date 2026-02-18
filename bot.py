import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import os

TOKEN = os.environ.get("BOT_TOKEN")

attendance_data = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attendance_data.clear()

    keyboard = [
        [InlineKeyboardButton("✅ Mark Attendance", callback_data="mark")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📢 Attendance Session Started!\n\n"
        "🕘 Click the button below to mark your attendance.",
        reply_markup=reply_markup
    )

async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if user.id not in attendance_data:
        attendance_data[user.id] = {
            "name": user.mention_html(),
            "time": datetime.now().strftime("%H:%M:%S")
        }

        await query.message.reply_html(
            f"✅ {attendance_data[user.id]['name']} marked attendance\n"
            f"🕒 Time: {attendance_data[user.id]['time']}"
        )
    else:
        await query.answer("⚠️ You already marked attendance!", show_alert=True)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not attendance_data:
        await update.message.reply_text("❌ No attendance marked today.")
        return

    text = "📋 Today's Attendance Report\n\n"

    for data in attendance_data.values():
        text += f"👤 {data['name']} | 🕒 {data['time']}\n"

    text += f"\n📊 Total Present: {len(attendance_data)}"

    await update.message.reply_html(text)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attendance_data.clear()
    await update.message.reply_text("🗑 Attendance cleared successfully.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start_attendance", start_attendance))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CallbackQueryHandler(mark_attendance))

    print("Bot is running...")
    await app.run_polling()

import asyncio

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
