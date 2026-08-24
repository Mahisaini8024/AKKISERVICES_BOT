import asyncio
import urllib.parse
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, CommandObject

from database import db
from config import CATEGORIES, ADMIN_USERNAME, BOT_USERNAME, REFERRAL_BONUS_POINTS
from handlers.relay_handlers import get_or_create_user_topic
from keyboards.inline_user import (
    main_menu_kb,
    demos_kb,
    explore_services_kb,
    categories_kb,
    services_list_kb,
    service_details_kb,
    contact_details_kb,
    referral_menu_kb,
    referral_back_kb,
    back_to_main_kb
)

logger = logging.getLogger(__name__)
user_router = Router()

def get_welcome_text(first_name: str) -> str:
    return (
        f"⚡ **`DIGITAL AKKI SERVICE BOT`** ⚡\n\n"
        f"👋 Welcome, **{first_name}**!\n\n"
        f"🔥 *Your #1 Partner for Telegram Growth, Automation & Web Solutions.*\n\n"
        f"💎 **What We Offer:**\n"
        f"• 🚀 **Telegram Growth** (Views, Reactions)\n"
        f"• 🤖 **Custom Bot Dev** (Aiogram 3, Auto)\n"
        f"• 📈 **Meta Ads** (High ROI & Mentorship)\n"
        f"• 💻 **Web & Panel Dev** (Landing Pages)\n\n"
        f"👨‍💻 **Developer:** @{ADMIN_USERNAME}\n"
        f"🛡️ *100% Genuine • Fast • 24/7 Support*\n\n"
        f"👇 *Select an option below to get started:* "
    )

async def _notify_admin_start_lead(bot: Bot, user, referrer_id, existing_user):
    admin_group_id = await db.get_admin_group_id()
    if admin_group_id:
        username_str = f"@{user.username}" if user.username else "No Username"
        ref_str = f"User ID `{referrer_id}`" if referrer_id else "Direct / Organic"
        thread_id = await get_or_create_user_topic(bot, admin_group_id, user, ref_str)
        
        clean_first_name = (user.first_name or "").replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
        clean_last_name = (user.last_name or "").replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
        lead_group_text = (
            f"🚀 **#NEW_LEAD**\n"
            f"👤 {clean_first_name} {clean_last_name} ({username_str})\n"
            f"🆔 `{user.id}` | 🎁 {ref_str}"
        )
        try:
            await bot.send_message(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                text=lead_group_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Could not send start lead alert to group: {e}")

@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    existing_user = await db.get_user(user.id)
    referrer_id = None
    
    # 1. Send Welcome Message INSTANTLY to User (0-Second Delay)
    welcome_text = get_welcome_text(user.first_name or "Client")
    await message.answer(
        text=welcome_text,
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )
    
    # 2. Async DB & Admin Group background tasks
    await db.add_or_update_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or ""
    )
    
    if not existing_user and command and command.args:
        ref_payload = command.args.strip()
        ref_id_str = ref_payload.replace("ref_", "")
        if ref_id_str.isdigit():
            referrer_id = int(ref_id_str)
            if referrer_id != user.id:
                success, _ = await db.process_referral(
                    new_user_id=user.id,
                    referrer_id=referrer_id,
                    points=REFERRAL_BONUS_POINTS
                )
                if success:
                    try:
                        await bot.send_message(
                            chat_id=referrer_id,
                            text=(
                                f"🎉 **NEW REFERRAL JOINED!** 🚀\n\n"
                                f"👤 **Friend:** {user.first_name} (@{user.username or 'N/A'})\n"
                                f"💰 **Reward:** `+{REFERRAL_BONUS_POINTS} Points` added to your wallet!\n\n"
                                f"👉 Tap **🎁 Refer & Earn** in the menu to check your balance."
                            ),
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.warning(f"Could not notify referrer {referrer_id}: {e}")

        await _notify_admin_start_lead(bot, user, referrer_id, existing_user)

@user_router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(
        f"🆔 **Your Telegram User ID:** `{message.from_user.id}`\n"
        f"👤 **Username:** @{message.from_user.username or 'N/A'}",
        parse_mode="Markdown"
    )

@user_router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery):
    await callback.answer()
    user = callback.from_user
    welcome_text = get_welcome_text(user.first_name or "Client")
    try:
        await callback.message.edit_text(
            text=welcome_text,
            reply_markup=main_menu_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=welcome_text,
            reply_markup=main_menu_kb(),
            parse_mode="Markdown"
        )

def get_service_order_link(service_name: str) -> str:
    msg = f"Hello Akki! I want to order: {service_name}"
    encoded = urllib.parse.quote(msg)
    return f"https://t.me/{ADMIN_USERNAME}?text={encoded}"

@user_router.callback_query(F.data == "explore_services")
async def cb_explore_services(callback: CallbackQuery):
    l1 = get_service_order_link("01. Prediction Auto Bot System")
    l2 = get_service_order_link("02. Auto Reaction, Views & Live Stream")
    l3 = get_service_order_link("03. Advanced Welcome Bot")
    l4 = get_service_order_link("04. Auto Forwarding System")
    l5 = get_service_order_link("05. Real Member Growth")
    l6 = get_service_order_link("06. Meta Ads Setup")
    l7 = get_service_order_link("07. Meta Ads Live Course")
    l8 = get_service_order_link("08. Group & Channel Trade")
    l9 = get_service_order_link("09. Hack & Control Panels")
    l10 = get_service_order_link("10. Web & Landing Pages")
    l11 = get_service_order_link("11. Custom Bot Development")

    text = (
        "⚡ **AKKI DIGITAL SERVICES** ⚡\n\n"
        "🔥 *Custom Bots • Automation • Growth • Web Dev*\n\n"
        "💎 **OUR SERVICES LIST:**\n\n"
        f"1️⃣ 🎯 **Prediction Auto Bot System** — [👉 ORDER NOW]({l1})\n"
        f"2️⃣ 🤖 **Auto Reactions & Views** — [👉 ORDER NOW]({l2})\n"
        f"3️⃣ 👋 **Advanced Welcome Bot** — [👉 ORDER NOW]({l3})\n"
        f"4️⃣ 🔄 **Auto Forwarding System** — [👉 ORDER NOW]({l4})\n"
        f"5️⃣ 👥 **Real Member Growth** — [👉 ORDER NOW]({l5})\n"
        f"6️⃣ 📈 **Meta Ads Setup** — [👉 ORDER NOW]({l6})\n"
        f"7️⃣ 🎓 **Meta Ads Live Course** — [👉 ORDER NOW]({l7})\n"
        f"8️⃣ 🏪 **Group & Channel Trade** — [👉 ORDER NOW]({l8})\n"
        f"9️⃣ 🛠️ **Hack & Control Panels** — [👉 ORDER NOW]({l9})\n"
        f"🔟 🌐 **Web & Landing Pages** — [👉 ORDER NOW]({l10})\n"
        f"1️⃣1️⃣ 🤖 **Custom Bot Development** — [👉 ORDER NOW]({l11})\n\n"
        "💡 **HAVE A CUSTOM IDEA?**\n"
        "Aapka koi bhi requirement ho, hum waisa bot banayenge! ⚡\n\n"
        f"💬 **Direct DM Order:** @{ADMIN_USERNAME}"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=explore_services_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=explore_services_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data.startswith("cat:"))
async def cb_category_selected(callback: CallbackQuery):
    cat_id = callback.data.split(":")[1]
    cat_info = CATEGORIES.get(cat_id)
    
    if not cat_info:
        await callback.answer("Category not found!", show_alert=True)
        return
    
    services = await db.get_services_by_category(cat_id)
    if not services:
        text = f"**{cat_info['title']}**\n\n⚠️ No active services in this category currently."
        await callback.message.edit_text(
            text=text,
            reply_markup=categories_kb(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    text = (
        f"**{cat_info['title']}**\n"
        f"_{cat_info['desc']}_\n\n"
        f"👇 **Select a service below to view full details & pricing:**"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=services_list_kb(cat_id, services),
        parse_mode="Markdown"
    )
    await callback.answer()

@user_router.callback_query(F.data.startswith("srv:"))
async def cb_service_detail(callback: CallbackQuery):
    service_code = callback.data.split(":")[1]
    service = await db.get_service_by_code(service_code)
    
    if not service:
        await callback.answer("Service details not found!", show_alert=True)
        return
    
    await callback.message.edit_text(
        text=service["full_desc"],
        reply_markup=service_details_kb(service["category_id"], service_code, service["title"]),
        parse_mode="Markdown"
    )
    await callback.answer()

@user_router.callback_query(F.data.startswith("lead:"))
async def cb_capture_lead(callback: CallbackQuery, bot: Bot):
    service_code = callback.data.split(":")[1]
    service = await db.get_service_by_code(service_code)
    
    if not service:
        await callback.answer("Service not found!", show_alert=True)
        return
    
    user = callback.from_user
    username_str = f"@{user.username}" if user.username else "No Username"
    
    # Save lead in DB
    await db.add_lead(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        service_code=service_code,
        service_title=service["title"]
    )
    
    # Send instant lead alert to all admins
    admins = await db.get_admins()
    alert_text = (
        f"🚨 **#SERVICE_INQUIRY**\n"
        f"👤 {user.first_name} ({username_str})\n"
        f"📦 `{service['title']}`"
    )
    
    for admin_id in admins:
        try:
            await bot.send_message(chat_id=admin_id, text=alert_text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not deliver lead notification to admin {admin_id}: {e}")

    # Send to Admin Group (Inside User's Topic)
    admin_group_id = await db.get_admin_group_id()
    if admin_group_id:
        thread_id = await get_or_create_user_topic(bot, admin_group_id, user)
        try:
            sent_grp = await bot.send_message(
                chat_id=admin_group_id,
                message_thread_id=thread_id,
                text=alert_text,
                parse_mode="Markdown"
            )
            await db.save_message_mapping(sent_grp.message_id, user.id, callback.message.message_id)
        except Exception as e:
            logger.warning(f"Could not deliver lead to admin group {admin_group_id}: {e}")
    
    await callback.answer(
        "✅ Notification sent to Akki! He will connect with you soon. You can also click below to chat directly on DM.",
        show_alert=True
    )

@user_router.callback_query(F.data == "contact_info")
async def cb_contact_info(callback: CallbackQuery):
    text = (
        "💬 **DOVELOPER AKKI — Direct Contact**\n\n"
        f"👤 **Name:** DOVELOPER AKKI 🖥️\n"
        f"💬 **Telegram Username:** @{ADMIN_USERNAME}\n"
        f"⚡ **Working Hours:** 24/7 Fast Response Guaranteed\n\n"
        "Feel free to drop a message directly on Telegram for quick deals, custom bot orders or bulk discounts!"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=contact_details_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=contact_details_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data == "about_developer")
async def cb_about_developer(callback: CallbackQuery):
    text = (
        "👨‍💻 **ABOUT DEVELOPER AKKI**\n\n"
        "⚡ *Full-Stack Bot Developer & Growth Expert*\n\n"
        "🛠️ **Core Expertise:**\n"
        "• 🤖 **Aiogram 3 & Python Bots** (Fast & Async)\n"
        "• 🚀 **Telegram Growth** (Reactions, Views, Members)\n"
        "• 📈 **Meta Ads Setup** (Low CPR & 1-on-1 Mentorship)\n"
        "• 💻 **Web & Panel Dev** (Custom UI & Backends)\n\n"
        "🌟 **Why Clients Trust Us:**\n"
        "✔️ 100% Genuine & High Retention\n"
        "✔️ 24/7 Fast Turnaround & Support\n"
        "✔️ Custom Solutions for Every Budget\n\n"
        f"💬 **Direct DM:** @{ADMIN_USERNAME}"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data == "demo_portfolio")
async def cb_demo_portfolio(callback: CallbackQuery):
    text = (
        "🧪 **LIVE DEMOS & PORTFOLIO SHOWCASE** 🚀\n\n"
        "Explore live working demos of bots and tools developed by **AKKI SERVICES**:\n\n"
        "📱 **1. Phone Number Info / OSINT Lookup Bot**\n"
        "• Instant lookup of caller details, operator & region.\n\n"
        "🛡️ **2. Welcome Guard & Captcha Bot**\n"
        "• Smart group protection with interactive math captcha & custom cards.\n\n"
        "🔄 **3. Auto Channel Forwarder & Cloner**\n"
        "• Real-time content forwarding without forward tags.\n\n"
        "🌐 **4. Mini App Web Store**\n"
        "• Modern Telegram glassmorphic store interface.\n\n"
        f"👇 *Tap any demo button below or contact @{ADMIN_USERNAME} for custom bots!*"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=demos_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=demos_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data == "price_calculator")
async def cb_price_calculator(callback: CallbackQuery):
    text = (
        "🟢 **AKKI SERVICES — PRICE & RATES CARD** 🟢\n\n"
        "⚡ *Best Market Rates • High Quality • Instant Start*\n\n"
        "🚀 **Telegram Marketing Rates:**\n"
        "• 👁️ **Post Views:** Starting @ ₹15 / 1,000 Views\n"
        "• ❤️ **Auto Reactions:** Starting @ ₹25 / 1,000 Reactions\n"
        "• 👥 **Targeted Members:** Starting @ ₹120 / 1,000 Members\n"
        "• 🛡️ **Channel Verification:** Custom Quote\n\n"
        "🤖 **Custom Bot Development:**\n"
        "• ⚡ **Aiogram 3 / Python Bot:** Starting @ ₹499\n"
        "• 🔐 **VIP Guard & Group Bot:** Starting @ ₹799\n"
        "• 🛍️ **Digital Store & Payment Bot:** Starting @ ₹1,199\n\n"
        "📈 **Meta Ads & Marketing:**\n"
        "• 🎯 **High ROI Campaign Setup:** Starting @ ₹999\n"
        "• 🎓 **1-on-1 Live Mentorship:** Starting @ ₹1,499\n\n"
        "💻 **Web & Panel Development:**\n"
        "• 🌐 **Modern Landing Page:** Starting @ ₹899\n"
        "• 🎮 **Custom Panel / Dashboard:** Starting @ ₹1,999\n\n"
        f"💬 *Bulk discounts available! Contact @{ADMIN_USERNAME} for quick orders.*"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data == "proofs_reviews")
async def cb_proofs_reviews(callback: CallbackQuery):
    text = (
        "🌟 **PROOFS & CLIENT REVIEWS** 🌟\n\n"
        "🏆 **Trusted by 500+ Clients & Communities**\n\n"
        "📊 **Our Performance Stats:**\n"
        "• ✅ **Orders Completed:** 1,200+\n"
        "• ⭐ **Average Rating:** 4.9 / 5.0\n"
        "• ⚡ **Average Delivery Time:** Under 15 Minutes\n"
        "• 🛡️ **Drop-Free Guarantee:** 100% Non-Drop\n\n"
        "💬 **Recent Client Feedback:**\n"
        "💬 *'Best bot developer on Telegram! Super fast delivery.'* — @Rohit_TG\n"
        "💬 *'Channel views & reactions delivered within 5 mins.'* — @CryptoxKing\n"
        "💬 *'Meta ads training helped scale my store 10x.'* — @AmanGrowth\n\n"
        f"👉 *Want live demo links or sample tests? Message @{ADMIN_USERNAME} directly!*"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data == "why_choose_us")
async def cb_why_choose_us(callback: CallbackQuery):
    text = (
        "🛡️ **WHY CHOOSE AKKI SERVICES?** 🛡️\n\n"
        "🔥 *We deliver excellence, speed, and 100% reliability for all digital needs.*\n\n"
        "💎 **Our Core Guarantees:**\n"
        "• ⚡ **Instant Delivery:** Automated high-speed processing.\n"
        "• 🛡️ **100% Safe & Anti-Ban:** Safe algorithms compliant with Telegram TOS.\n"
        "• 💰 **Unbeatable Pricing:** Direct developer rates without middlemen.\n"
        "• 🔄 **Lifetime Drop Protection:** Free refill on eligible services.\n"
        "• 👨‍💻 **Dedicated Support:** 24/7 one-on-one developer assistance.\n\n"
        f"💬 *Ready to get started? Chat directly with @{ADMIN_USERNAME}!*"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=back_to_main_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data == "refer_and_earn")
async def cb_refer_and_earn(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    bot_info = await bot.get_me()
    bot_username = bot_info.username or BOT_USERNAME
    
    stats = await db.get_user_referral_stats(user.id)
    ref_link = f"https://t.me/{bot_username}?start=ref_{user.id}"
    
    text = (
        "🎁 **AKKI SERVICES — REFER & EARN PROGRAM** 🚀\n\n"
        "Share your exclusive referral link with friends, groups & channels. Earn points on every invite and redeem them for free Telegram members, reactions, post views, or cash discounts on custom orders!\n\n"
        f"🔗 **Your Unique Referral Link:**\n`{ref_link}`\n\n"
        f"📊 **Your Referral Stats:**\n"
        f"👥 **Friends Invited:** `{stats['referral_count']}`\n"
        f"💰 **Wallet Points Balance:** `{stats['points']} Points`\n\n"
        "⚡ **How It Works:**\n"
        f"1. Copy & share your link with friends.\n"
        f"2. When they start the bot, you instantly get **+{REFERRAL_BONUS_POINTS} Points**.\n"
        "3. Redeem points for free services or direct project discounts!\n\n"
        "👇 *Tap below to share link or view leaderboard:* "
    )
    
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=referral_menu_kb(bot_username, user.id),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=referral_menu_kb(bot_username, user.id),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    await callback.answer()

@user_router.callback_query(F.data == "ref_leaderboard")
async def cb_ref_leaderboard(callback: CallbackQuery):
    top_users = await db.get_top_referrers(limit=10)
    
    if not top_users:
        text = (
            "🏆 **REFERRAL LEADERBOARD** 🏆\n\n"
            "No referrals recorded yet! Be the first to share your link and top the leaderboard! 🚀"
        )
    else:
        text = "🏆 **TOP REFERRAL CHAMPIONS** 🏆\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for idx, u in enumerate(top_users):
            medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
            name = u['first_name'] or "User"
            username_str = f"(@{u['username']})" if u['username'] else ""
            text += f"{medal} **{name}** {username_str} — `{u['referral_count']} Invites` ({u['points']} Pts)\n"
        
        text += "\n🔥 *Invite more friends to climb to the top!*"
    
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=referral_back_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=referral_back_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@user_router.callback_query(F.data == "ref_redeem")
async def cb_ref_redeem(callback: CallbackQuery):
    stats = await db.get_user_referral_stats(callback.from_user.id)
    text = (
        "💰 **REDEEM YOUR REFERRAL POINTS** 💰\n\n"
        f"💼 **Your Current Balance:** `{stats['points']} Points`\n\n"
        "🎯 **Redemption Rewards:**\n"
        "• ⚡ **100 Points:** 100 Auto Reactions / 1,000 Post Views\n"
        "• 👥 **250 Points:** 50 Real Targeted Members\n"
        "• 💵 **500+ Points:** Direct ₹ Cash Discount on Custom Bots / Meta Ads / Web Dev\n\n"
        f"👉 To redeem your points, contact **@{ADMIN_USERNAME}** directly with your User ID (`{callback.from_user.id}`)."
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=referral_back_kb(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=referral_back_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()
