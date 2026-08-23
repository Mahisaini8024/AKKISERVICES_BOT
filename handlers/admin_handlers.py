import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import db
from utils.states import BroadcastStates
from keyboards.inline_admin import (
    admin_panel_kb,
    admin_services_list_kb,
    admin_broadcast_confirm_kb,
    admin_back_kb
)

logger = logging.getLogger(__name__)
admin_router = Router()

def get_admin_dashboard_text(user_count: int, leads_count: int) -> str:
    return (
        "👑 **DOVELOPER AKKI — ADMIN PANEL** 👑\n\n"
        "Welcome to the management control center.\n\n"
        f"👥 **Total Registered Users:** `{user_count}`\n"
        f"📈 **Total Leads Generated:** `{leads_count}`\n\n"
        "👇 *Select an admin action below:* "
    )

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    if not await db.is_admin(user_id):
        await message.answer(
            "⛔ **Access Denied!**\n\n"
            "You are not registered as an administrator.\n"
            "If you are the bot owner, claim access with `/claimadmin <password>`",
            parse_mode="Markdown"
        )
        return
    
    users_cnt = await db.get_user_count()
    leads_cnt = await db.get_leads_count()
    
    await message.answer(
        text=get_admin_dashboard_text(users_cnt, leads_cnt),
        reply_markup=admin_panel_kb(),
        parse_mode="Markdown"
    )

@admin_router.callback_query(F.data == "admin_back_panel")
async def cb_admin_back_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    if not await db.is_admin(user_id):
        await callback.answer("Access Denied!", show_alert=True)
        return
    
    users_cnt = await db.get_user_count()
    leads_cnt = await db.get_leads_count()
    
    try:
        await callback.message.edit_text(
            text=get_admin_dashboard_text(users_cnt, leads_cnt),
            reply_markup=admin_panel_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=get_admin_dashboard_text(users_cnt, leads_cnt),
            reply_markup=admin_panel_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Access Denied!", show_alert=True)
        return
    
    users_cnt = await db.get_user_count()
    leads_cnt = await db.get_leads_count()
    admins = await db.get_admins()
    
    text = (
        "📊 **BOT DETAILED STATISTICS**\n\n"
        f"👥 **Total Unique Users:** `{users_cnt}`\n"
        f"🎯 **Total Service Inquiries / Leads:** `{leads_cnt}`\n"
        f"👑 **Active Admins Count:** `{len(admins)}`\n\n"
        "⚡ All systems operating normally."
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=admin_back_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_recent_leads")
async def cb_recent_leads(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Access Denied!", show_alert=True)
        return
    
    leads = await db.get_recent_leads(limit=10)
    if not leads:
        await callback.message.edit_text(
            "📋 **Recent Leads**\n\nNo leads recorded yet.",
            reply_markup=admin_back_kb(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    lines = ["📋 **RECENT 10 CLIENT LEADS**\n"]
    for idx, l in enumerate(leads, 1):
        uname = f"@{l['username']}" if l["username"] else "No Username"
        date_str = str(l["created_at"])[:16]
        lines.append(
            f"**{idx}. {l['first_name']}** ({uname})\n"
            f"🆔 `{l['user_id']}` | 🕒 {date_str}\n"
            f"📦 Service: `{l['service_title']}`\n"
        )
    
    text = "\n".join(lines)
    await callback.message.edit_text(
        text=text,
        reply_markup=admin_back_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_referral_stats")
async def cb_admin_referral_stats(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Access Denied!", show_alert=True)
        return

    ref_summary = await db.get_referral_stats_admin()
    top_users = await db.get_top_referrers(limit=10)

    text = (
        "🎁 **REFERRAL PROGRAM ADMIN STATS** 📊\n\n"
        f"🔗 **Total Successful Referrals:** `{ref_summary['total_referrals']}`\n"
        f"💰 **Total Reward Points Distributed:** `{ref_summary['total_points_awarded']} Pts`\n\n"
    )

    if top_users:
        text += "🏆 **Top 10 Referrers:**\n"
        for idx, u in enumerate(top_users, 1):
            uname = f"@{u['username']}" if u["username"] else "No Username"
            text += f"{idx}. **{u['first_name']}** ({uname}) — `{u['referral_count']} Invites` ({u['points']} Pts)\n"
    else:
        text += "ℹ️ No referrals recorded yet."

    await callback.message.edit_text(
        text=text,
        reply_markup=admin_back_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_services")
async def cb_admin_services(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Access Denied!", show_alert=True)
        return
    
    services = await db.get_all_services_admin()
    text = (
        "📦 **MANAGE SERVICES & VISIBILITY**\n\n"
        "Tap on any service below to toggle it **Active (🟢)** or **Inactive (🔴)** for users:"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=admin_services_list_kb(services),
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_toggle:"))
async def cb_toggle_service(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Access Denied!", show_alert=True)
        return
    
    srv_id = int(callback.data.split(":")[1])
    await db.toggle_service_status(srv_id)
    
    services = await db.get_all_services_admin()
    text = (
        "📦 **MANAGE SERVICES & VISIBILITY**\n\n"
        "Status updated! Tap on any service below to toggle:"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=admin_services_list_kb(services),
        parse_mode="Markdown"
    )
    await callback.answer("Service status updated!")

# Broadcast Flow
@admin_router.callback_query(F.data == "admin_broadcast")
async def cb_start_broadcast(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Access Denied!", show_alert=True)
        return
    
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text(
        "📢 **BROADCAST ANNOUNCEMENT**\n\n"
        "Send the message (Text, Photo, Video, Document, etc.) that you want to broadcast to all bot users.\n\n"
        "👉 Or send `/cancel` to abort.",
        reply_markup=admin_back_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_router.message(BroadcastStates.waiting_for_message, Command("cancel"))
async def cmd_cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Broadcast cancelled.", reply_markup=admin_panel_kb())

@admin_router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    await state.update_data(broadcast_chat_id=message.chat.id, broadcast_message_id=message.message_id)
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    
    users_cnt = await db.get_user_count()
    await message.answer(
        f"📢 **BROADCAST PREVIEW READY**\n\n"
        f"This message will be sent to **{users_cnt} users**.\n\n"
        f"Are you sure you want to send it now?",
        reply_markup=admin_broadcast_confirm_kb(),
        parse_mode="Markdown"
    )

@admin_router.callback_query(BroadcastStates.waiting_for_confirmation, F.data == "admin_confirm_broadcast")
async def cb_confirm_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    from_chat_id = data.get("broadcast_chat_id")
    message_id = data.get("broadcast_message_id")
    
    await state.clear()
    await callback.message.edit_text("⏳ **Broadcasting in progress... Please wait.**", parse_mode="Markdown")
    
    users = await db.get_all_users()
    success = 0
    failed = 0
    
    for u in users:
        target_user_id = u["user_id"]
        try:
            await bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            success += 1
            await asyncio.sleep(0.04) # Prevent hitting rate limits
        except Exception as e:
            logger.debug(f"Broadcast failed for user {target_user_id}: {e}")
            failed += 1
    
    result_text = (
        "✅ **BROADCAST COMPLETED**\n\n"
        f"📤 **Sent Successfully:** `{success}`\n"
        f"🚫 **Failed / Blocked:** `{failed}`\n"
        f"👥 **Total Targets:** `{len(users)}`"
    )
    await callback.message.answer(text=result_text, reply_markup=admin_panel_kb(), parse_mode="Markdown")
    await callback.answer()

@admin_router.callback_query(BroadcastStates.waiting_for_confirmation, F.data == "admin_cancel_broadcast")
async def cb_cancel_broadcast_btn(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled.", reply_markup=admin_panel_kb())
    await callback.answer()
