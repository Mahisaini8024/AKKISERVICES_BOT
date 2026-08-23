from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Bot Stats & Leads", callback_data="admin_stats"),
            InlineKeyboardButton(text="📋 Recent 10 Leads", callback_data="admin_recent_leads")
        ],
        [
            InlineKeyboardButton(text="🎁 Referral Stats", callback_data="admin_referral_stats"),
            InlineKeyboardButton(text="📢 Broadcast to Users", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="📦 Toggle Services (Active/Off)", callback_data="admin_services")
        ],
        [
            InlineKeyboardButton(text="🏠 Switch to Client View", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_services_list_kb(services: list) -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        status_icon = "🟢" if s["is_active"] else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {s['title'][:32]}...",
                callback_data=f"admin_toggle:{s['id']}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="admin_back_panel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Send Broadcast Now", callback_data="admin_confirm_broadcast"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="admin_cancel_broadcast")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_back_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="admin_back_panel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
