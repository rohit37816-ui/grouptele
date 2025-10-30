from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from collections import defaultdict
import time

# Your bot token and admin Telegram user ID
TOKEN = "7811920862:AAHK1fodIKSt1sboyu4O4xU_PBybtIsbFtk"
ADMIN_ID = 6065778458    # e.g., 123456789

# Data stores for stats and spam tracking
user_first_message = defaultdict(bool)
user_message_timestamps = defaultdict(list)
group_stats = defaultdict(lambda: {'joins': 0, 'leaves': 0})
KEYWORDS = ['spam', 'advertisement', 'sale', 'http', 'www']
FLOOD_LIMIT = 5
FLOOD_SECONDS = 10

async def on_new_member(update, context):
    chat = update.effective_chat
    group_stats[chat.id]['joins'] += 1
    for user in update.message.new_chat_members:
        isbot = "Yes" if user.is_bot else "No"
        msg = (
            f"👤 New member joined:\n"
            f"Name: {user.full_name}\n"
            f"Username: @{user.username if user.username else 'No Username'}\n"
            f"Profile: [{user.full_name}](tg://user?id={user.id})\n"
            f"Bot: {isbot}\n"
            f"Group: {chat.title if chat.title else ''}\n"
            f"Group username: @{chat.username if chat.username else 'No Username'}\n"
            f"Group ID: {chat.id}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
        user_first_message[user.id] = False

async def on_member_left(update, context):
    chat = update.effective_chat
    group_stats[chat.id]['leaves'] += 1
    user = update.message.left_chat_member
    msg = (
        f"🔴 Member left:\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'No Username'}\n"
        f"Profile: [{user.full_name}](tg://user?id={user.id})\n"
        f"Group: {chat.title if chat.title else ''}\n"
        f"Group username: @{chat.username if chat.username else 'No Username'}\n"
        f"Group ID: {chat.id}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")

async def on_message(update, context):
    chat = update.effective_chat
    user = update.effective_user
    # First message alert
    if user.id in user_first_message and not user_first_message[user.id]:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👀 First message from [{user.full_name}](tg://user?id={user.id}) in {chat.title if chat.title else ''} (@{chat.username if chat.username else 'No Username'})",
            parse_mode="Markdown"
        )
        user_first_message[user.id] = True

    # Flood/spam alert
    now = time.time()
    timestamps = user_message_timestamps[user.id]
    timestamps.append(now)
    user_message_timestamps[user.id] = [t for t in timestamps if now - t < FLOOD_SECONDS]
    if len(user_message_timestamps[user.id]) > FLOOD_LIMIT:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 Spam alert: [{user.full_name}](tg://user?id={user.id}) sent many messages quickly in {chat.title if chat.title else ''} (@{chat.username if chat.username else 'No Username'})",
            parse_mode="Markdown"
        )

    # Keyword detection alert
    text = update.message.text.lower() if update.message and update.message.text else ""
    if any(word in text for word in KEYWORDS):
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔑 Keyword alert in {chat.title if chat.title else ''}: Message from [{user.full_name}](tg://user?id={user.id}):\n{text}",
            parse_mode="Markdown"
        )

async def on_edit(update, context):
    chat = update.effective_chat
    user = update.edited_message.from_user
    msg = (
        f"✏️ Message edited in {chat.title if chat.title else ''} (@{chat.username if chat.username else 'No Username'}):\n"
        f"User: [{user.full_name}](tg://user?id={user.id})\n"
        f"New text: {update.edited_message.text}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")

async def on_pin(update, context):
    chat = update.effective_chat
    pinner = update.effective_user
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(f"📌 Message pinned in {chat.title if chat.title else ''} (@{chat.username if chat.username else 'No Username'}) by "
              f"[{pinner.full_name}](tg://user?id={pinner.id})"),
        parse_mode="Markdown"
    )

# Command: /groups - lists all monitored groups
async def groups_command(update, context):
    msg = "Groups I'm monitoring:\n"
    for group_id in group_stats:
        msg += f"- {group_id}\n"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

# Command: /stats - shows joins/leaves stats per group
async def stats_command(update, context):
    msg = "Group Stats:\n"
    for group_id, stats in group_stats.items():
        msg += (f"Group {group_id}: Joins={stats['joins']}, "
                f"Leaves={stats['leaves']}\n")
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

# NOTE: Detecting deleted messages is not possible with Bot API

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL, on_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_member_left))
    app.add_handler(MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, on_pin))
    app.add_handler(MessageHandler(filters.ALL & filters.UpdateType.EDITED_MESSAGE, on_edit))
    app.add_handler(CommandHandler("groups", groups_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.run_polling()
