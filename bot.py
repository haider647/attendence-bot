import logging
from datetime import datetime, timedelta
from telegram import Update, Chat
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
import os

# ====== CONFIG ======
TOKEN = os.environ.get("BOT_TOKEN")
attendance_data = {}  # {user_id: {"name":..., "username":..., "time":...}}

# ====== LOGGING ======
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ====== TIMEZONE ======
def pakistan_time():
    return datetime.utcnow() + timedelta(hours=5)

# ====== ADMIN CHECK ======
async def is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ["administrator", "creator"]

# ====== MESSAGE HANDLER ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only respond in groups
    if update.effective_chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        return  # Ignore private chats

    text = update.message.text.strip()
    user = update.effective_user

    if text == "1":
        # Mark attendance
        if user.id not in attendance_data:
            attendance_data[user.id] = {
                "name": user.full_name,
                "username": f"@{user.username}" if user.username else "N/A",
                "time": pakistan_time().strftime("%H:%M:%S")
            }
            await update.message.reply_html(
                f"✅ <b>{attendance_data[user.id]['name']}</b> "
                f"(<i>{attendance_data[user.id]['username']}</i>) marked attendance!\n"
                f"🕒 <b>Time (PKT):</b> {attendance_data[user.id]['time']}"
            )
        else:
            await update.message.reply_text("⚠️ You already marked attendance!")

    elif text == "2":
        # Show report (admins only)
        if not await is_group_admin(update, context):
            await update.message.reply_text("❌ Only group admins can use this command.")
            return
        if not attendance_data:
            await update.message.reply_text("❌ No attendance has been marked yet.")
            return
        sorted_attendance = sorted(attendance_data.items(), key=lambda x: x[1]["time"])
        report_text = "📋 <b>Today's Attendance Report</b>\n\n"
        for i, (_, data) in enumerate(sorted_attendance, start=1):
            report_text += (
                f"📝 <b>{i}.</b> {data['name']} (<i>{data['username']}</i>) | "
                f"🕒 {data['time']}\n"
            )
        report_text += f"\n📊 <b>Total Present:</b> {len(attendance_data)}"
        await update.message.reply_html(report_text)

    elif text == "3":
        # Clear attendance (admins only)
        if not await is_group_admin(update, context):
            await update.message.reply_text("❌ Only group admins can use this command.")
            return
        attendance_data.clear()
        await update.message.reply_text("🗑 Attendance has been cleared successfully!")

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # Handle all text messages (number commands)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🚀 Bot is running...")
    app.run_polling(poll_interval=3, timeout=60)

if __name__ == "__main__":
    main()
