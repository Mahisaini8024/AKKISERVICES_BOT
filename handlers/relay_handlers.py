import re
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, ReactionTypeEmoji, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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
    existing_thread_id = await db.get_user_thread_id(user.id)
    if existing_thread_id:
        return existing_thread_id

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

        username_str = f"@{user.username}" if user.username else "No Username"
        profile_card = (
            f"👤 **Client:** {user.first_name} {user.last_name or ''} ({username_str})\n"
            f"🆔 **ID:** `{user.id}` | 🎁 **Source:** {referrer_str}\n"
            f"💬 *Reply in this topic to chat with client.*"
        )
        
        action_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Send Notice", callback_data=f"btn_bc_single:{user.id}"),
                InlineKeyboardButton(text="🚥 Change Status", callback_data=f"btn_status_menu:{user.id}")
            ]
        ])

        header_msg = await bot.send_message(
            chat_id=group_id,
            message_thread_id=thread_id,
            text=profile_card,
            reply_markup=action_kb,
            parse_mode="Markdown"
        )
        try:
            await bot.pin_chat_message(chat_id=group_id, message_id=header_msg.message_id)
        except Exception:
            pass
        return thread_id
    except Exception as e:
        logger.warning(f"Could not create forum topic for user {user.id} in group {group_id}: {e}")
        return await db.get_admin_thread_id()

# -------------------------------------------------------------
# 1. GROUP COMMANDS & SETTINGS (EVALUATED FIRST)
# -------------------------------------------------------------

@relay_router.message(F.chat.type == ChatType.PRIVATE, Command("setgroup", "setadmingroup"))
async def cmd_set_group_dm(message: Message, command: CommandObject):
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
# 2. BROADCAST & CONTROL PANEL COMMANDS
# -------------------------------------------------------------

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
import csv

def admin_control_reply_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="📅 Today Users"),
            KeyboardButton(text="📊 All Users")
        ],
        [
            KeyboardButton(text="🔍 Search UID"),
            KeyboardButton(text="📢 Broadcast")
        ],
        [
            KeyboardButton(text="📬 Export"),
            KeyboardButton(text="📈 Stats"),
            KeyboardButton(text="📋 Approved UIDs")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@relay_router.message(Command("panel", "admin", "bcpanel"))
async def cmd_admin_panel_group(message: Message):
    await message.reply(
        "🎛️ **Admin Control Panel** ──────────────────\n"
        "Select an option using the buttons below:",
        reply_markup=admin_control_reply_kb(),
        parse_mode="Markdown"
    )

# -------------------------------------------------------------
# 2.1 ADMIN REPLY KEYBOARD BUTTON HANDLERS
# -------------------------------------------------------------

@relay_router.message(F.text == "📅 Today Users")
async def handle_btn_today_users(message: Message):
    count = await db.get_today_users_count()
    today_list = await db.get_today_users()
    text = f"📅 **TODAY'S NEW USERS ({count})** ⚡\n──────────────────\n"
    if today_list:
        for u in today_list[:15]:
            un = f"@{u['username']}" if u['username'] else "No Username"
            text += f"• `{u['user_id']}` | {u['first_name']} ({un})\n"
    else:
        text += "No new users joined today yet."
    await message.reply(text, parse_mode="Markdown")

@relay_router.message(F.text == "📊 All Users")
async def handle_btn_all_users(message: Message):
    count = await db.get_user_count()
    users = await db.get_all_users()
    text = f"📊 **TOTAL REGISTERED USERS ({count})** ⚡\n──────────────────\n"
    for u in users[:15]:
        un = f"@{u['username']}" if u['username'] else "No Username"
        text += f"• `{u['user_id']}` | {u['first_name']} ({un})\n"
    if count > 15:
        text += f"\n*...and {count - 15} more users.*"
    await message.reply(text, parse_mode="Markdown")

@relay_router.message(F.text == "🔍 Search UID")
async def handle_btn_search_uid(message: Message):
    await message.reply(
        "🔍 **SEARCH USER BY UID:**\n\n"
        "User ko search karne ke liye command use karein:\n"
        "`/user <User_ID>` (e.g. `/user 6556791395`)",
        parse_mode="Markdown"
    )

@relay_router.message(F.text == "📢 Broadcast")
async def handle_btn_broadcast(message: Message):
    await message.reply(
        "📢 **ALL USERS BROADCAST MODE** 🚀\n\n"
        "Is message ko **REPLY** karke wo Text, Photo ya Video bhejein jo aap **SABHI USERS** ko broadcast karna chahte hain!\n\n"
        "*(ya `# General` me `/broadcast <your_text>` likhein)*",
        parse_mode="Markdown"
    )

@relay_router.message(F.text == "📬 Export")
async def handle_btn_export(message: Message):
    users = await db.get_all_users_full()
    csv_path = "users_export.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Username", "First Name", "Last Name", "Points", "Referrals", "Joined At"])
        for u in users:
            writer.writerow([u["user_id"], u["username"] or "", u["first_name"] or "", u["last_name"] or "", u["points"], u["referral_count"], u["joined_at"]])
    
    doc = FSInputFile(csv_path)
    await message.reply_document(
        document=doc,
        caption=f"📬 **ALL USERS CSV EXPORT**\nTotal Records: `{len(users)}` Users",
        parse_mode="Markdown"
    )

@relay_router.message(F.text == "📈 Stats")
async def handle_btn_stats(message: Message):
    total_users = await db.get_user_count()
    today_users = await db.get_today_users_count()
    ref_stats = await db.get_referral_stats_admin()
    text = (
        "📈 **EXECUTIVE BOT STATISTICS** ⚡\n"
        "──────────────────\n"
        f"👥 **Total Registered Users:** `{total_users}`\n"
        f"📅 **New Users Today:** `{today_users}`\n"
        f"🎁 **Total Referrals Processed:** `{ref_stats['total_referrals']}`\n"
        f"💎 **Total Referral Points:** `{ref_stats['total_points_awarded']}`\n"
        "──────────────────\n"
        "🟢 **Bot Health:** 100% Operational (Render Cloud 24/7)"
    )
    await message.reply(text, parse_mode="Markdown")

@relay_router.message(F.text == "📋 Approved UIDs")
async def handle_btn_approved_uids(message: Message):
    text = (
        "📋 **APPROVED ADMINS & UIDs** 🛡️\n"
        "──────────────────\n"
        f"👑 **Owner / Super Admin:** @{ADMIN_USERNAME}\n"
        "✅ **Status:** Authorized & Approved"
    )
    await message.reply(text, parse_mode="Markdown")

@relay_router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), Command("broadcast", "bc", "sendall"))
async def cmd_broadcast_group(message: Message, command: CommandObject, bot: Bot):
    thread_id = message.message_thread_id
    text_to_send = command.args
    reply_msg = message.reply_to_message

    if not text_to_send and not reply_msg:
        usage = (
            "📢 **BROADCAST SYSTEM USAGE:**\n\n"
            "• **All Users Broadcast (General Topic):**\n"
            "  `/broadcast Hello Everyone! New services added in Bot!`\n"
            "  *ya kisi photo/video ko reply karke `/broadcast` likhein.*\n\n"
            "• **Single Client Personal Broadcast (User Topic me):**\n"
            "  User topic ke andar `/broadcast <text>` chalane par sirf us specific client ko announcement card jayega!"
        )
        msg = await message.reply(usage, parse_mode="Markdown")
        asyncio.create_task(delete_after(msg, 10))
        return

    target_user_id = None
    if thread_id:
        target_user_id = await db.get_user_by_thread_id(thread_id)

    # SCENARIO 1: SINGLE USER BROADCAST (Inside User Topic)
    if target_user_id:
        try:
            if reply_msg:
                await bot.copy_message(
                    chat_id=target_user_id,
                    from_chat_id=message.chat.id,
                    message_id=reply_msg.message_id
                )
            else:
                card_text = (
                    f"📢 **OFFICIAL ANNOUNCEMENT FROM AKKI SERVICES** ⚡\n\n"
                    f"{text_to_send}\n\n"
                    f"💬 Contact Developer: @{ADMIN_USERNAME}"
                )
                await bot.send_message(
                    chat_id=target_user_id,
                    text=card_text,
                    parse_mode="Markdown"
                )
            
            conf = await message.reply(f"✅ **Personal Broadcast Notice Sent to Client!** (ID: `{target_user_id}`)", parse_mode="Markdown")
            asyncio.create_task(delete_after(conf, 4))
        except Exception as e:
            err = await message.reply(f"❌ **Failed to send to client:** `{e}`", parse_mode="Markdown")
            asyncio.create_task(delete_after(err, 5))
        return

    # SCENARIO 2: ALL USERS BROADCAST (General / Main Group)
    users = await db.get_all_users()
    if not users:
        msg = await message.reply("⚠️ Database me koi users nahi mile.", parse_mode="Markdown")
        asyncio.create_task(delete_after(msg, 5))
        return

    status_msg = await message.reply(f"⏳ **Broadcasting message to {len(users)} users...**", parse_mode="Markdown")

    success_count = 0
    fail_count = 0

    for u in users:
        uid = u["user_id"]
        try:
            if reply_msg:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=message.chat.id,
                    message_id=reply_msg.message_id
                )
            else:
                card_text = (
                    f"📢 **AKKI SERVICES ANNOUNCEMENT** ⚡\n\n"
                    f"{text_to_send}\n\n"
                    f"💬 Direct DM: @{ADMIN_USERNAME}"
                )
                await bot.send_message(
                    chat_id=uid,
                    text=card_text,
                    parse_mode="Markdown"
                )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    report = (
        "📢 **BROADCAST COMPLETED!** 🚀\n"
        "─────────────────────────\n"
        f"✅ **Delivered:** `{success_count}` Users\n"
        f"❌ **Failed/Blocked:** `{fail_count}` Users\n"
        f"👥 **Total Reached:** `{len(users)}` Users"
    )
    await status_msg.edit_text(report, parse_mode="Markdown")

# -------------------------------------------------------------
# 3. TOPIC STATUS SYSTEM (/status)
# -------------------------------------------------------------

STATUS_CONFIG = {
    "lead": ("🟡", "LEAD", "NEW LEAD"),
    "1": ("🟡", "LEAD", "NEW LEAD"),
    "deal": ("💬", "DISCUSSING", "DISCUSSING REQUIREMENT"),
    "2": ("💬", "DISCUSSING", "DISCUSSING REQUIREMENT"),
    "paid": ("💰", "PAID", "PAID CLIENT"),
    "3": ("💰", "PAID", "PAID CLIENT"),
    "progress": ("🚀", "IN DEV", "PROJECT IN DEVELOPMENT"),
    "4": ("🚀", "IN DEV", "PROJECT IN DEVELOPMENT"),
    "done": ("✅", "DONE", "PROJECT COMPLETED"),
    "5": ("✅", "DONE", "PROJECT COMPLETED"),
    "hold": ("⏸️", "HOLD", "ON HOLD"),
    "6": ("⏸️", "HOLD", "ON HOLD"),
    "closed": ("🔒", "CLOSED", "TOPIC CLOSED"),
    "7": ("🔒", "CLOSED", "TOPIC CLOSED")
}

def topic_status_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="🟡 Lead", callback_data="tstatus:lead"),
            InlineKeyboardButton(text="💬 Discussing", callback_data="tstatus:deal")
        ],
        [
            InlineKeyboardButton(text="💰 Paid", callback_data="tstatus:paid"),
            InlineKeyboardButton(text="🚀 In Dev", callback_data="tstatus:progress")
        ],
        [
            InlineKeyboardButton(text="✅ Done", callback_data="tstatus:done"),
            InlineKeyboardButton(text="⏸️ On Hold", callback_data="tstatus:hold")
        ],
        [
            InlineKeyboardButton(text="🔒 Close Topic", callback_data="tstatus:closed")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@relay_router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), Command("status"))
async def cmd_topic_status(message: Message, command: CommandObject, bot: Bot):
    thread_id = message.message_thread_id
    if not thread_id:
        msg = await message.reply("⚠️ `/status` command ko kisi user ke topic ke andar bhejein!", parse_mode="Markdown")
        asyncio.create_task(delete_after(msg, 5))
        return

    target_user_id = await db.get_user_by_thread_id(thread_id)
    if not target_user_id:
        msg = await message.reply("⚠️ Yeh topic kisi registered user se linked nahi hai.", parse_mode="Markdown")
        asyncio.create_task(delete_after(msg, 5))
        return

    args = (command.args or "").strip().lower().split()
    
    if not args:
        await message.reply(
            "🚥 **SELECT TOPIC STATUS:**\n\nChoose a status below to rename & update this client topic:",
            reply_markup=topic_status_kb(),
            parse_mode="Markdown"
        )
        return

    status_key = args[0]
    notify_user = len(args) > 1 and args[1] in ["notify", "yes", "true", "pm"]
    
    await apply_topic_status(bot, message.chat.id, thread_id, target_user_id, status_key, notify_user, message)

async def apply_topic_status(bot: Bot, group_id: int, thread_id: int, user_id: int, status_key: str, notify_user: bool, trigger_msg: Message = None):
    if status_key not in STATUS_CONFIG:
        if trigger_msg:
            msg = await trigger_msg.reply(
                "⚠️ **Invalid Status!** Use:\n"
                "• `/status 1` (Lead) | `/status 2` (Discussing)\n"
                "• `/status 3` (Paid) | `/status 4` (In Dev)\n"
                "• `/status 5` (Done) | `/status 6` (Hold) | `/status 7` (Closed)",
                parse_mode="Markdown"
            )
            asyncio.create_task(delete_after(msg, 6))
        return

    emoji, badge, full_status = STATUS_CONFIG[status_key]
    user = await db.get_user(user_id)
    user_name = user["first_name"] if user and user.get("first_name") else "Client"
    
    new_topic_name = f"{emoji} 👤 {user_name[:18]} [{badge}]"
    try:
        await bot.edit_forum_topic(
            chat_id=group_id,
            message_thread_id=thread_id,
            name=new_topic_name
        )
    except Exception as e:
        logger.warning(f"Could not edit topic name: {e}")

    if trigger_msg:
        conf = await trigger_msg.reply(f"✅ **Topic Status Updated:** {emoji} `{full_status}`", parse_mode="Markdown")
        asyncio.create_task(delete_after(conf, 3))

    if notify_user:
        try:
            user_msg = (
                f"🚦 **PROJECT STATUS UPDATE** ⚡\n\n"
                f"📌 **Status:** {emoji} **{full_status}**\n"
                f"💬 Contact Developer: @{ADMIN_USERNAME}"
            )
            await bot.send_message(
                chat_id=user_id,
                text=user_msg,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Could not notify user of status update: {e}")

# -------------------------------------------------------------
# 4. CALLBACK QUERY HANDLERS FOR INLINE BUTTONS
# -------------------------------------------------------------

@relay_router.callback_query(F.data.startswith("tstatus:"))
async def cb_topic_status_selected(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    status_key = callback.data.split(":")[1]
    thread_id = callback.message.message_thread_id
    if not thread_id:
        return
    
    target_user_id = await db.get_user_by_thread_id(thread_id)
    if not target_user_id:
        return
        
    await apply_topic_status(bot, callback.message.chat.id, thread_id, target_user_id, status_key, False, callback.message)

@relay_router.callback_query(F.data.startswith("btn_bc_single:"))
async def cb_btn_bc_single(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.data.split(":")[1]
    prompt = (
        f"📢 **PERSONAL CLIENT BROADCAST MODE** ⚡\n\n"
        f"Is message ko **REPLY** karke text, photo ya video bhejein — wo DIRECT User ID `{user_id}` ko Official Notice card ki tarah deliver hoga!\n\n"
        f"*(ya `/broadcast <your_text>` likhein)*"
    )
    await callback.message.reply(prompt, parse_mode="Markdown")

@relay_router.callback_query(F.data.startswith("btn_status_menu:"))
async def cb_btn_status_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.reply(
        "🚥 **SELECT TOPIC STATUS:**\n\nChoose a status below to rename & update this client topic:",
        reply_markup=topic_status_kb(),
        parse_mode="Markdown"
    )

@relay_router.callback_query(F.data == "btn_bc_all_prompt")
async def cb_btn_bc_all_prompt(callback: CallbackQuery):
    await callback.answer()
    prompt = (
        "📢 **ALL USERS BROADCAST MODE** 🚀\n\n"
        "Is message ko **REPLY** karke wo Text, Photo ya Video bhejein jo aap **SABHI USERS** ko broadcast karna chahte hain!\n\n"
        "*(ya `# General` me `/broadcast <your_text>` likhkar send karein)*"
    )
    await callback.message.reply(prompt, parse_mode="Markdown")

# -------------------------------------------------------------
# 5. ADMIN MESSAGES IN USER TOPICS (RELAID TO CLIENT DM)
# -------------------------------------------------------------

@relay_router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def handle_group_admin_message(message: Message, bot: Bot):
    # Ignore slash commands
    if message.text and message.text.startswith("/"):
        return

    target_user_id = None
    if message.message_thread_id:
        target_user_id = await db.get_user_by_thread_id(message.message_thread_id)

    if not target_user_id and message.reply_to_message:
        replied_msg = message.reply_to_message
        target_user_id = await db.get_user_by_group_message_id(replied_msg.message_id)

        if not target_user_id:
            search_text = replied_msg.text or replied_msg.caption or ""
            id_match = re.search(r"(?:User ID|ID)[:\s]+`?(\d{5,})`?", search_text, re.IGNORECASE)
            if id_match:
                target_user_id = int(id_match.group(1))

    if not target_user_id:
        return

    # Check if this message is a reply to an All-User Broadcast prompt or Personal Broadcast prompt
    if message.reply_to_message and message.reply_to_message.text:
        reply_text = message.reply_to_message.text
        if "ALL USERS BROADCAST MODE" in reply_text:
            # Trigger all user broadcast with this message
            users = await db.get_all_users()
            if not users:
                msg = await message.reply("⚠️ Database me koi users nahi mile.", parse_mode="Markdown")
                asyncio.create_task(delete_after(msg, 5))
                return

            status_msg = await message.reply(f"⏳ **Broadcasting message to {len(users)} users...**", parse_mode="Markdown")
            success_count = 0
            fail_count = 0

            for u in users:
                uid = u["user_id"]
                try:
                    await bot.copy_message(
                        chat_id=uid,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id
                    )
                    success_count += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    fail_count += 1

            report = (
                "📢 **BROADCAST COMPLETED!** 🚀\n"
                "─────────────────────────\n"
                f"✅ **Delivered:** `{success_count}` Users\n"
                f"❌ **Failed/Blocked:** `{fail_count}` Users\n"
                f"👥 **Total Reached:** `{len(users)}` Users"
            )
            await status_msg.edit_text(report, parse_mode="Markdown")
            return

        elif "PERSONAL CLIENT BROADCAST MODE" in reply_text:
            # Trigger single user broadcast card with this message
            try:
                if message.text:
                    card_text = (
                        f"📢 **OFFICIAL ANNOUNCEMENT FROM AKKI SERVICES** ⚡\n\n"
                        f"{message.text}\n\n"
                        f"💬 Contact Developer: @{ADMIN_USERNAME}"
                    )
                    await bot.send_message(
                        chat_id=target_user_id,
                        text=card_text,
                        parse_mode="Markdown"
                    )
                else:
                    await bot.copy_message(
                        chat_id=target_user_id,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id
                    )
                conf = await message.reply(f"✅ **Personal Broadcast Notice Sent to Client!** (ID: `{target_user_id}`)", parse_mode="Markdown")
                asyncio.create_task(delete_after(conf, 4))
                return
            except Exception as e:
                err = await message.reply(f"❌ **Failed to send:** `{e}`", parse_mode="Markdown")
                asyncio.create_task(delete_after(err, 5))
                return

    # Normal 1-on-1 chat relay to client PM
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

        try:
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[ReactionTypeEmoji(emoji="👍")]
            )
        except Exception:
            pass

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
# 6. USER PM MESSAGES (RELAID TO FORUM TOPIC)
# -------------------------------------------------------------

@relay_router.message(F.chat.type == ChatType.PRIVATE)
async def handle_user_pm_message(message: Message, bot: Bot):
    if message.text and message.text.startswith("/"):
        return

    user = message.from_user
    admin_group_id = await db.get_admin_group_id()

    if not admin_group_id:
        await message.reply(
            f"💬 *Message received! DM: @{ADMIN_USERNAME}*",
            parse_mode="Markdown"
        )
        return

    thread_id = await get_or_create_user_topic(bot, admin_group_id, user)

    try:
        sent_group_msg = None

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
            await db.save_message_mapping(
                group_message_id=sent_group_msg.message_id,
                user_id=user.id,
                user_message_id=message.message_id
            )

        try:
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[ReactionTypeEmoji(emoji="👍")]
            )
        except Exception:
            pass

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
