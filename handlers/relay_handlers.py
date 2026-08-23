import re
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.filters import Command, CommandObject
from aiogram.enums import ChatType

from database import db
from config import ADMIN_USERNAME

logger = logging.getLogger(__name__)
relay_router = Router()

async def delete_after(message: Message, delay_seconds: int = 3):
    """Automatically delete a message after specified seconds"""
    try:
        await asyncio.sleep(delay_seconds)
        await message.delete()
    except Exception:
        pass

# -------------------------------------------------------------
# HELPER: GET OR CREATE FORUM TOPIC FOR A USER
# -------------------------------------------------------------

async def get_or_create_user_topic(bot: Bot, group_id: int, user, referrer_str: str = "Direct") -> int | None:
    """Get existing forum topic ID for user or automatically create a new one"""
    # 1. Check if user already has a topic in DB
    existing_thread_id = await db.get_user_thread_id(user.id)
    if existing_thread_id:
        return existing_thread_id

    # 2. Try to create a clean topic name (only Name, no User ID)
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    clean_name = full_name[:25] if full_name else "Client"
    topic_name = f"👤 {clean_name}"

    try:
        topic = await bot.create_forum_topic(
            chat_id=group_id,
            name=topic_name
        )
        thread_id = topic.message_thread_id
        await db.save_user_topic(user.id, thread_id)

        # Short & clean profile header
        username_str = f"@{user.username}" if user.username else "No Username"
        profile_card = (
            f"👤 **Client:** {user.first_name} {user.last_name or ''} ({username_str})\n"
            f"🆔 **ID:** `{user.id}` | 🎁 **Source:** {referrer_str}\n"
            f"💬 *Reply in this topic to chat with client.*"
        )
        await bot.send_message(
            chat_id=group_id,
            message_thread_id=thread_id,
            text=profile_card,
            parse_mode="Markdown"
        )
        return thread_id
    except Exception as e:
        logger.warning(f"Could not create forum topic for user {user.id} in group {group_id}: {e}")
        return await db.get_admin_thread_id()

# -------------------------------------------------------------
# 1. GROUP COMMANDS & SETTINGS
# -------------------------------------------------------------

@relay_router.message(F.chat.type == ChatType.PRIVATE, Command("setgroup", "setadmingroup"))
async def cmd_set_group_dm(message: Message, command: CommandObject):
    """Handle /setgroup in Private DM"""
    args = command.args
    if args and (args.strip().startswith("-") or args.strip().isdigit()):
        try:
            group_id = int(args.strip())
            await db.set_admin_group_id(group_id)
            await message.reply(
                f"✅ **Admin Group ID set to:** `{group_id}`",
                parse_mode="Markdown"
            )
            return
        except ValueError:
            pass

    await message.reply(
        "⚠️ **`/setgroup` ko apne Group ke andar send karein!**\n\n"
        "1. Apne group (**THE AKKI SERVICES BOT**) me jayein.\n"
        "2. Wahan `/setgroup` likh kar send karein.",
        parse_mode="Markdown"
    )

@relay_router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), Command("setgroup", "setadmingroup"))
async def cmd_set_group(message: Message):
    """Set current group as the main admin notification & live chat relay group"""
    group_id = message.chat.id
    group_title = message.chat.title or "Admin Group"
    thread_id = message.message_thread_id
    
    await db.set_admin_group_id(group_id)
    await db.set_admin_thread_id(thread_id)
    
    response_text = (
        "✅ **Group Linked Successfully!** 🚀\n\n"
        f"👥 **Group:** `{group_title}`\n"
        f"🆔 **ID:** `{group_id}`\n\n"
        "• Har new user ka **Personal Topic** auto create hoga.\n"
        "• Topic me direct reply karke aap user se chat kar sakte hain."
    )
    await message.reply(response_text, parse_mode="Markdown")

@relay_router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), Command("groupid", "id"))
async def cmd_group_id(message: Message):
    await message.reply(
        f"🆔 **Group ID:** `{message.chat.id}`",
        parse_mode="Markdown"
    )

# -------------------------------------------------------------
# 2. ADMIN SENDS MESSAGE IN TOPIC OR REPLIES -> DELIVER TO USER IN PM
# -------------------------------------------------------------

@relay_router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def handle_group_admin_message(message: Message, bot: Bot):
    # Ignore commands
    if message.text and message.text.startswith("/"):
        return

    # Check if message is inside a user's dedicated topic
    target_user_id = None
    if message.message_thread_id:
        target_user_id = await db.get_user_by_thread_id(message.message_thread_id)

    # If not a topic message, check if it is a reply to a forwarded message
    if not target_user_id and message.reply_to_message:
        replied_msg = message.reply_to_message
        target_user_id = await db.get_user_by_group_message_id(replied_msg.message_id)

        # Fallback: Parse User ID from message text or caption
        if not target_user_id:
            search_text = replied_msg.text or replied_msg.caption or ""
            id_match = re.search(r"(?:User ID|ID)[:\s]+`?(\d{5,})`?", search_text, re.IGNORECASE)
            if id_match:
                target_user_id = int(id_match.group(1))

    if not target_user_id:
        return  # Not in a user topic and not a reply to user

    # Deliver message to user in PM (Clean & Direct)
    try:
        if message.text:
            await bot.send_message(
                chat_id=target_user_id,
                text=message.text,
                parse_mode="Markdown"
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=target_user_id,
                photo=message.photo[-1].file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.video:
            await bot.send_video(
                chat_id=target_user_id,
                video=message.video.file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.voice:
            await bot.send_voice(
                chat_id=target_user_id,
                voice=message.voice.file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.document:
            await bot.send_document(
                chat_id=target_user_id,
                document=message.document.file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.sticker:
            await bot.send_sticker(chat_id=target_user_id, sticker=message.sticker.file_id)
        else:
            await bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

        # Auto Like Reaction on Admin's Message
        try:
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[ReactionTypeEmoji(emoji="👍")]
            )
        except Exception:
            pass

        # Short delivery confirmation in group (auto-deleted in 3s)
        confirm_group = await message.reply("✅ *Sent*", parse_mode="Markdown")
        asyncio.create_task(delete_after(confirm_group, 3))
    except Exception as e:
        logger.error(f"Failed to send admin reply to user {target_user_id}: {e}")
        err_msg = await message.reply(
            f"❌ **Failed:** `{e}`",
            parse_mode="Markdown"
        )
        asyncio.create_task(delete_after(err_msg, 5))

# -------------------------------------------------------------
# 3. USER SENDS MESSAGE IN PM -> FORWARD INTO USER'S TOPIC (SHORT & CLEAN)
# -------------------------------------------------------------

@relay_router.message(F.chat.type == ChatType.PRIVATE)
async def handle_user_pm_message(message: Message, bot: Bot):
    # Ignore slash commands (they are handled by user_router)
    if message.text and message.text.startswith("/"):
        return

    user = message.from_user
    admin_group_id = await db.get_admin_group_id()

    if not admin_group_id:
        # If group is not linked yet
        await message.reply(
            f"💬 *Message received! DM: @{ADMIN_USERNAME}*",
            parse_mode="Markdown"
        )
        return

    # Get or automatically create user topic in the group
    thread_id = await get_or_create_user_topic(bot, admin_group_id, user)

    try:
        sent_group_msg = None

        # Send clean message directly into the topic without bulky headers
        if message.text:
            sent_group_msg = await bot.send_message(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                text=message.text,
                parse_mode="Markdown"
            )
        elif message.photo:
            sent_group_msg = await bot.send_photo(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                photo=message.photo[-1].file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.video:
            sent_group_msg = await bot.send_video(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                video=message.video.file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.voice:
            sent_group_msg = await bot.send_voice(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                voice=message.voice.file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.document:
            sent_group_msg = await bot.send_document(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                document=message.document.file_id,
                caption=message.caption or "",
                parse_mode="Markdown"
            )
        elif message.sticker:
            sent_group_msg = await bot.send_sticker(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                sticker=message.sticker.file_id
            )
        else:
            sent_group_msg = await bot.copy_message(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

        if sent_group_msg:
            # Save mapping so replies in the group can also be tracked
            await db.save_message_mapping(
                group_message_id=sent_group_msg.message_id,
                user_id=user.id,
                user_message_id=message.message_id
            )

        # Auto Like Reaction on User's Message
        try:
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[ReactionTypeEmoji(emoji="👍")]
            )
        except Exception:
            pass

        # Short confirmation to user (auto-deleted in 3s)
        confirm_user = await message.reply(
            "✅ *Message sent to Akki!*",
            parse_mode="Markdown"
        )
        asyncio.create_task(delete_after(confirm_user, 3))
    except Exception as e:
        logger.error(f"Error relaying user message to admin group: {e}")
        fallback_msg = await message.reply(
            f"💬 *Message received! DM: @{ADMIN_USERNAME}*",
            parse_mode="Markdown"
        )
        asyncio.create_task(delete_after(fallback_msg, 5))
