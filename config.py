import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8201462668:AAH5vsUyMAA-GCxZlYK2FZK5LaH9YwumQFs")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Developerakki").replace("@", "")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "")
DB_PATH = os.getenv("DB_PATH", "bot_database.db")
BOT_USERNAME = os.getenv("BOT_USERNAME", "akkiservices_official_bot")
REFERRAL_BONUS_POINTS = int(os.getenv("REFERRAL_BONUS_POINTS", "10"))

raw_admin_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(i.strip()) for i in raw_admin_ids.split(",") if i.strip().isdigit()]

# Service Categories
CATEGORIES = {
    "tg_growth": {
        "title": "🚀 Telegram Growth & Marketing",
        "desc": "Boost your channels & groups with real active members, reactions, views and streaming power!"
    },
    "tg_bots": {
        "title": "🤖 Telegram Bots & Automation",
        "desc": "Custom smart Telegram bots for automation, management, forwarders and high performance."
    },
    "meta_ads": {
        "title": "📈 Meta Ads & Live Training",
        "desc": "Scale your business, channel or app with high ROI Facebook/Instagram Ads & 1-on-1 Training."
    },
    "web_dev": {
        "title": "💻 Web & Custom Panel Development",
        "desc": "High speed landing pages, full scale websites, gaming hack panels & custom software."
    }
}

# 10 Main Services with Detailed Specifications
DEFAULT_SERVICES = [
    # 1. Telegram Growth
    {
        "code": "auto_reactions_views",
        "category_id": "tg_growth",
        "title": "⚡ Auto Reactions, Views & Live Stream Members",
        "short_desc": "Instant custom emoji reactions, guaranteed views, & live stream audience.",
        "full_desc": (
            "🔥 **Auto Reactions, Views & Live Stream Members Service**\n\n"
            "Maximize your Telegram channel engagement and look 100% authentic!\n\n"
            "✨ **Key Features:**\n"
            "• ⚡ Instant Auto Reactions (👍, ❤️, 🔥, 🎉, 🚀 & Custom Emojis)\n"
            "• 👁️ High-Speed Post Views (Natural Delivery Speed)\n"
            "• 🔴 Telegram Live Stream Members (Stable & Long Retention)\n"
            "• 🛡️ 100% Safe & Drop-Free Guaranteed\n"
            "• 📊 Works for Unlimited Channel Posts\n\n"
            "⚡ **Delivery:** Instant Activation (5-15 mins)\n"
            "💰 **Pricing:** Best Competitive Rates (Custom plans available)"
        )
    },
    {
        "code": "real_members_adding",
        "category_id": "tg_growth",
        "title": "👥 Real Genuine Members Adding",
        "short_desc": "Filtered, active & high-quality targeted Telegram members addition.",
        "full_desc": (
            "👥 **Real Genuine Members Adding Service**\n\n"
            "Add high quality, active, targeted members directly to your Telegram group!\n\n"
            "✨ **Key Features:**\n"
            "• 🎯 Target specific niche/competitor groups\n"
            "• ⚡ Filtered online & recently active users only\n"
            "• 🛡️ Anti-Ban & Safe Adding Methods\n"
            "• 📈 Fast turnaround with zero group restrictions\n"
            "• 💯 Boost group activity, discussions & sales conversion\n\n"
            "⚡ **Delivery:** 1k to 50k+ members delivered smoothly\n"
            "💰 **Pricing:** Budget-friendly bulk packages available"
        )
    },
    {
        "code": "group_channel_trade",
        "category_id": "tg_growth",
        "title": "📢 Group & Channel Marketplace (Buy & Sell)",
        "short_desc": "Aged, active, verified Telegram groups & channels with clean history.",
        "full_desc": (
            "📢 **Telegram Group & Channel Buy/Sell Service**\n\n"
            "Looking to buy an established Telegram channel/group or sell yours at best valuation?\n\n"
            "✨ **Key Features:**\n"
            "• 🏆 100% Verified & Aged Channels (2018 - 2024)\n"
            "• 🔒 Safe Escrow & Complete Ownership Transfer (with Primary SIM/Number)\n"
            "• 📊 Active niches available: Crypto, Trading, Tech, Movies, Gaming & General\n"
            "• 🚫 Clean history with zero copyright or scam strikes\n\n"
            "⚡ **Delivery:** Instant Ownership Transfer\n"
            "💰 **Pricing:** Based on member count, age & niche"
        )
    },

    # 2. Telegram Bots & Automation
    {
        "code": "welcome_bot_adv",
        "category_id": "tg_bots",
        "title": "🛡️ Welcome Bot with Advance Features",
        "short_desc": "Smart captcha verification, custom banners, button menus & auto-clean.",
        "full_desc": (
            "🛡️ **Advance Welcome & Group Guard Bot**\n\n"
            "Automate your group welcome messages, protect from spammers and look super professional!\n\n"
            "✨ **Key Features:**\n"
            "• 🤖 Interactive Captcha Verification (Math, Button, Image)\n"
            "• 🖼️ Custom Welcome Cards / Dynamic Image Generation with user name & photo\n"
            "• 🔘 Clickable Inline Buttons (Rules, Channel Links, Support)\n"
            "• 🧹 Auto-Delete Service & Left Messages (Keeps group clean)\n"
            "• ⏱️ Custom Auto-Timed delete for welcome messages\n\n"
            "⚡ **Deployment:** 24/7 Cloud Hosted with zero downtime\n"
            "💰 **Pricing:** One-time setup / Monthly hosting options"
        )
    },
    {
        "code": "auto_forwarding_sys",
        "category_id": "tg_bots",
        "title": "🔄 Auto Forwarding System",
        "short_desc": "Real-time auto forwarder between private/public channels without forward tag.",
        "full_desc": (
            "🔄 **Telegram Auto Forwarding & Cloning System**\n\n"
            "Clone or mirror content from any source channel/group to your own channel seamlessly!\n\n"
            "✨ **Key Features:**\n"
            "• ⚡ Instant 0-second Delay Real-Time Forwarding\n"
            "• 🚫 Removes 'Forwarded From' tag (posts look 100% original)\n"
            "• ✂️ Replace/Remove watermarks, links, keywords & usernames automatically\n"
            "• 📁 Supports All Media: Photos, Videos, Documents, Audio, Voice, Polls\n"
            "• 🔒 Works with Restricted & Private Channels (Content saving restricted)\n\n"
            "⚡ **Delivery:** Complete setup on your own server/bot\n"
            "💰 **Pricing:** Affordable one-time / subscription"
        )
    },
    {
        "code": "custom_tracking_bot",
        "category_id": "tg_bots",
        "title": "🎯 Custom Advance Features & Tracking Bot Development",
        "short_desc": "Tailor-made bots with custom database, tracking, analytics & prediction logic.",
        "full_desc": (
            "🎯 **Custom High-Performance Telegram Bot Development**\n\n"
            "Get a 100% custom-coded bot built for your exact business requirements!\n\n"
            "✨ **Capabilities & Use Cases:**\n"
            "• 📊 Live Data Tracking, Analytics & Activity Monitoring Bots\n"
            "• 🎰 Prediction, Calculation & Algorithm Bots (Fast & Accurate)\n"
            "• 💳 Payment Gateway / Crypto Bot Integrations (USDT, TON, UPI)\n"
            "• 🗄️ SQLite / PostgreSQL / MongoDB integrated backends\n"
            "• 👑 Full Admin Dashboard & Broadcast Systems\n\n"
            "⚡ **Tech Stack:** Python (Aiogram 3), Node.js, Fast Async APIs\n"
            "💰 **Pricing:** Quote based on project scope"
        )
    },

    # 3. Meta Ads & Marketing Training
    {
        "code": "meta_ads_advance",
        "category_id": "meta_ads",
        "title": "🎯 Meta Ads Advance Campaign Setup",
        "short_desc": "High-converting Facebook & Instagram ads for Telegram channels, apps & business.",
        "full_desc": (
            "🎯 **Meta Ads (Facebook & Instagram) Advance Campaign Service**\n\n"
            "Get high volume, laser-targeted leads and channel members at lowest cost per result (CPR)!\n\n"
            "✨ **What's Included:**\n"
            "• 🚀 Laser-targeted Audience Research & Competitor Insights\n"
            "• 🎨 High CTR Ad Creatives (Videos, Graphics, High-converting Ad Copies)\n"
            "• 📈 Deep-linking setup for Direct 1-Click Telegram joins\n"
            "• 🛡️ Anti-Ban / Cloaking guidance & Safe Page Setup\n"
            "• 📊 Continuous A/B Testing & Daily Campaign Optimization\n\n"
            "⚡ **Results:** Maximum ROI & scalable member growth\n"
            "💰 **Pricing:** Management fee / Percentage or fixed setup"
        )
    },
    {
        "code": "meta_ads_course_live",
        "category_id": "meta_ads",
        "title": "🎓 Meta Ads Course & Live 1-on-1 Training",
        "short_desc": "Complete practical live training on FB/Insta ads, scaling, bypass & lowest CPR.",
        "full_desc": (
            "🎓 **Meta Ads Complete Live Mastery Course**\n\n"
            "Master Facebook & Instagram Ads from scratch to advanced scaling through live 1-on-1 sessions!\n\n"
            "✨ **Course Curriculum:**\n"
            "• 📚 Module 1: Business Manager, Ad Accounts & Pixel Mastery\n"
            "• 📚 Module 2: High Converting Creatives & Copywriting Strategies\n"
            "• 📚 Module 3: Advanced Audience Targeting, Lookalikes & Retargeting\n"
            "• 📚 Module 4: Running Telegram Channel Growth Ads at Lowest Cost\n"
            "• 📚 Module 5: Policy Compliance, Ban Prevention & Account Recovery\n"
            "• 🤝 Lifetime Support & Private VIP Community Access\n\n"
            "⚡ **Format:** Live Screenshare Sessions + Recorded Notes & Lifetime Q&A\n"
            "💰 **Pricing:** Special Discounted Course Fee"
        )
    },

    # 4. Web & Custom Panel Development
    {
        "code": "landing_big_website",
        "category_id": "web_dev",
        "title": "🌐 Landing Page & Full Big Website Development",
        "short_desc": "Modern, lightning-fast responsive websites, landing pages & enterprise web portals.",
        "full_desc": (
            "🌐 **Landing Page & Full-Scale Web Development**\n\n"
            "Build stunning, high-converting and ultra-fast websites for your brand or business!\n\n"
            "✨ **Features & Tech:**\n"
            "• 📱 100% Mobile & Desktop Responsive Design\n"
            "• ⚡ Lightning-Fast Page Load Speeds (Next.js, React, Tailwind, HTML5/CSS3)\n"
            "• 💳 Payment Gateway, Contact Forms, WhatsApp/Telegram chat integration\n"
            "• 🔒 SSL Secured, SEO Optimized & Google Indexed\n"
            "• 🎛️ Easy Admin Dashboard for content management\n\n"
            "⚡ **Turnaround:** 2 to 5 Days\n"
            "💰 **Pricing:** Customized according to website requirements"
        )
    },
    {
        "code": "hack_panel_gaming",
        "category_id": "web_dev",
        "title": "🕹️ Gaming Hack Panel / Custom Panel Development",
        "short_desc": "Custom admin panels, gaming UI/UX, key injection, user management & security.",
        "full_desc": (
            "🕹️ **Gaming Panel & Custom Control Panel Development**\n\n"
            "Complete end-to-end custom panel development with powerful management backend!\n\n"
            "✨ **Features:**\n"
            "• 🔑 License Key Generation (Hourly, Daily, Weekly, Monthly, Lifetime)\n"
            "• 🛡️ HWID Lock, Device Reset & Device Management\n"
            "• 📊 Reseller Panel System with balance & key credits\n"
            "• ⚡ Fast & Secure API Endpoints with Anti-Crack encryption\n"
            "• 🎨 Sleek Modern UI/UX Design (Dark Mode & Cyberpunk themes)\n\n"
            "⚡ **Tech:** Full source code + Server setup included\n"
            "💰 **Pricing:** Discuss scope on DM"
        )
    }
]
