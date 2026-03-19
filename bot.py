import logging
from datetime import datetime, timedelta
from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os

# ===== CONFIG =====
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 7966395775  # <-- apna Telegram numeric ID yahan dalen

attendance_data = {}  # {chat_id: {"open": bool, "users": {}}}

logging.basicConfig(level=logging.INFO)

# ===== TIME FUNCTION =====
def pakistan_time():
    pkt = datetime.utcnow() + timedelta(hours=5)
    return pkt.strftime("%I:%M %p").lstrip("0")  # Example: 3:13 PM

# ===== ESCAPE MARKDOWN =====
def escape_markdown(text: str) -> str:
    """
    Escape all Markdown special characters to prevent formatting issues.
    """
    if not text:
        return ""
    escape_chars = "\\_*[]()~`>#+-=|{}.!"
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

# ===== ADMIN CHECK =====
async def is_admin(update: Update):
    try:
        member = await update.effective_chat.get_member(update.effective_user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ===== MAIN HANDLER =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Only group chats
        if update.effective_chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
            return

        chat_id = update.effective_chat.id
        text = update.message.text.strip()
        user = update.effective_user

        # ===== OWNER CHECK =====
        try:
            owner_member = await update.effective_chat.get_member(OWNER_ID)
            if owner_member.status in ["left", "kicked"]:
                await update.effective_chat.leave()
                return
        except:
            await update.effective_chat.leave()
            return

        # Initialize group if first time
        if chat_id not in attendance_data:
            attendance_data[chat_id] = {"open": False, "users": {}}

        group = attendance_data[chat_id]

        # ===== OPEN ATTENDANCE =====
        if text.lower() == "attendance type 1":
            if not await is_admin(update):
                await update.message.reply_text("❌ Admins only.")
                return

            group["open"] = True
            group["users"].clear()
            await update.message.reply_text(
                "🟢 *Attendance Opened*\nMembers can mark attendance by sending: 1",
                parse_mode="Markdown"
            )

        # ===== CLOSE ATTENDANCE =====
        elif text.lower() == "attendance closed":
            if not await is_admin(update):
                await update.message.reply_text("❌ Admins only.")
                return

            group["open"] = False
            await update.message.reply_text(
                "🔴 *Attendance Closed*\nNo more entries will be accepted.",
                parse_mode="Markdown"
            )

        # ===== MARK ATTENDANCE =====
        elif text == "1":
            if not group["open"]:
                return  # silently ignore if attendance closed

            if user.id not in group["users"]:
                group["users"][user.id] = {
                    "name": user.full_name,
                    "username": user.username,  # Save Telegram @username
                    "time": pakistan_time()
                }
                username_text = f" (@{escape_markdown(user.username)})" if user.username else ""
                await update.message.reply_text(
                    f"✅ {escape_markdown(user.full_name)}{username_text} marked at {group['users'][user.id]['time']}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"⚠️ Already marked at {group['users'][user.id]['time']}",
                    parse_mode="Markdown"
                )

        # ===== REPORT =====
        elif text == "2":
            if not await is_admin(update):
                await update.message.reply_text("❌ Admins only.")
                return

            if not group["users"]:
                await update.message.reply_text("No attendance recorded.")
                return

            report = "📋 *Attendance Report*\n\n"
            for i, data in enumerate(group["users"].values(), 1):
                username_text = f" (@{escape_markdown(data['username'])})" if data.get("username") else ""
                report += f"{i}️⃣ *{escape_markdown(data['name'])}*{username_text} ✅ — {data['time']}\n"
            report += f"\n👥 *Total Present:* {len(group['users'])}"

            await update.message.reply_text(report, parse_mode="Markdown")

        # ===== CLEAR ATTENDANCE =====
        elif text == "3":
            if not await is_admin(update):
                await update.message.reply_text("❌ Admins only.")
                return
            group["users"].clear()
            await update.message.reply_text("🗑 *Attendance cleared*", parse_mode="Markdown")

    except Exception as e:
        logging.error(e)

# ===== START BOT =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
    print("🚀 Stable Attendance Bot Running (Owner + Admin Control)...")
    app.run_polling()

if __name__ == "__main__":
    main()
