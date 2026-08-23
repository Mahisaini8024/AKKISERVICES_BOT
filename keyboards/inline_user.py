import urllib.parse
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import CATEGORIES, ADMIN_USERNAME

WEBAPP_URL = "https://akkiservices-bot.onrender.com"

def get_prefilled_dm_url(service_title: str) -> str:
    msg = f"Hello Akki! I want to order: {service_title}"
    encoded = urllib.parse.quote(msg)
    return f"https://t.me/{ADMIN_USERNAME}?text={encoded}"

def main_menu_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="📱 Open Digital Store (Mini App)",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(
                text="🚀 Explore All Services",
                callback_data="explore_services"
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Chat on DM",
                url=f"https://t.me/{ADMIN_USERNAME}"
            ),
            InlineKeyboardButton(
                text="👨‍💻 About Akki",
                callback_data="about_developer"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def demos_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="📱 Number Info / OSINT Bot Demo",
                url="https://t.me/trucall_tbbot"
            )
        ],
        [
            InlineKeyboardButton(
                text="🛡️ Welcome Guard & Captcha Bot",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Auto Forwarder System Demo",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Order Custom Bot on DM",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Back to Main Menu",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def explore_services_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="💬 Chat on DM (@Developerakki)",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Back to Main Menu",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def categories_kb() -> InlineKeyboardMarkup:
    cat_icons = {
        "tg_services": "🚀",
        "bot_dev": "🤖",
        "meta_ads": "📈",
        "web_dev": "💻"
    }
    buttons = []
    for cat_id, cat_data in CATEGORIES.items():
        icon = cat_icons.get(cat_id, "📦")
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {cat_data['title']}",
                callback_data=f"cat:{cat_id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="💬 Chat on DM (@Developerakki)",
            url=f"https://t.me/{ADMIN_USERNAME}"
        )
    ])
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Back to Main Menu",
            callback_data="back_to_main"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def services_list_kb(category_id: str, services: list) -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        buttons.append([
            InlineKeyboardButton(
                text=f"⚡ {s['title']}",
                callback_data=f"srv:{s['code']}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="⬅️ Back", callback_data="explore_services"),
        InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_details_kb(category_id: str, service_code: str, service_title: str = "") -> InlineKeyboardMarkup:
    prefilled_url = get_prefilled_dm_url(service_title) if service_title else f"https://t.me/{ADMIN_USERNAME}"
    keyboard = [
        [
            InlineKeyboardButton(
                text="💬 Order on DM (Pre-Filled)",
                url=prefilled_url
            )
        ],
        [
            InlineKeyboardButton(
                text="⚡ Notify Akki (I'm Interested)",
                callback_data=f"lead:{service_code}"
            )
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data=f"cat:{category_id}"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def contact_details_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="💬 Chat on DM (@Developerakki)",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚀 Explore Services",
                callback_data="explore_services"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Back to Main Menu",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def referral_menu_kb(bot_username: str, user_id: int) -> InlineKeyboardMarkup:
    share_msg = "🔥 Join AKKI SERVICES for Telegram Growth, Auto Reactions, Custom Bots & Meta Ads!"
    encoded_text = urllib.parse.quote(share_msg)
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=ref_{user_id}&text={encoded_text}"
    
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Share Invite Link", url=share_url)
        ],
        [
            InlineKeyboardButton(text="🏆 Leaderboard", callback_data="ref_leaderboard"),
            InlineKeyboardButton(text="💰 Redeem Points", callback_data="ref_redeem")
        ],
        [
            InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def referral_back_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="refer_and_earn"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_main_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="💬 Chat on DM", url=f"https://t.me/{ADMIN_USERNAME}"),
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
