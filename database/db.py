import aiosqlite
import logging
from config import DB_PATH, DEFAULT_SERVICES, ADMIN_IDS, ADMIN_GROUP_ID

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database schema and seed default data"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    referrer_id INTEGER DEFAULT NULL,
                    points INTEGER DEFAULT 0,
                    referral_count INTEGER DEFAULT 0,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned INTEGER DEFAULT 0
                )
            """)

            # Referrals table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER UNIQUE,
                    points_rewarded INTEGER DEFAULT 10,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Settings table (for dynamic admin group id, configs, etc.)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Message Mappings table (for 2-way chat relay between users and admin group)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_message_id INTEGER UNIQUE,
                    user_id INTEGER,
                    user_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User Forum Topics table (for individual user topics in admin forum group)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_topics (
                    user_id INTEGER PRIMARY KEY,
                    thread_id INTEGER UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migration: Ensure new columns exist in existing users table
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in await cursor.fetchall()]
            if "referrer_id" not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT NULL")
            if "points" not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
            if "referral_count" not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
            if "is_banned" not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")

            # Admins table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Services table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    category_id TEXT,
                    title TEXT,
                    short_desc TEXT,
                    full_desc TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Leads / Inquiries table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    first_name TEXT,
                    service_code TEXT,
                    service_title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert initial admin IDs from config if any
            for admin_id in ADMIN_IDS:
                await db.execute(
                    "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
                    (admin_id,)
                )

            # Check if services already exist
            cursor = await db.execute("SELECT COUNT(*) FROM services")
            count = (await cursor.fetchone())[0]

            if count == 0:
                for s in DEFAULT_SERVICES:
                    await db.execute("""
                        INSERT OR IGNORE INTO services (code, category_id, title, short_desc, full_desc, is_active)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (s["code"], s["category_id"], s["title"], s["short_desc"], s["full_desc"]))
                logger.info("Default 10 services seeded successfully into database.")

            await db.commit()

    # User Methods
    async def add_or_update_user(self, user_id: int, username: str, first_name: str, last_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name
            """, (user_id, username, first_name, last_name))
            await db.commit()

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT user_id, username, first_name, last_name, referrer_id, points, referral_count, joined_at FROM users WHERE user_id = ?",
                (user_id,)
            )
            return await cursor.fetchone()

    async def get_user_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            users_map = {}
            # 1. Fetch from users table
            try:
                cursor = await db.execute("SELECT user_id, username, first_name FROM users")
                rows = await cursor.fetchall()
                for r in rows:
                    users_map[r["user_id"]] = {
                        "user_id": r["user_id"],
                        "username": r["username"] or "",
                        "first_name": r["first_name"] or "Client"
                    }
            except Exception as e:
                logger.warning(f"Error fetching users: {e}")

            # 2. Fetch from user_topics table
            try:
                cursor = await db.execute("SELECT user_id FROM user_topics")
                rows = await cursor.fetchall()
                for r in rows:
                    uid = r["user_id"]
                    if uid not in users_map:
                        users_map[uid] = {
                            "user_id": uid,
                            "username": "",
                            "first_name": "Client"
                        }
            except Exception as e:
                logger.warning(f"Error fetching user_topics: {e}")

            return list(users_map.values())

    async def get_all_users_full(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT user_id, username, first_name, last_name, points, referral_count, joined_at FROM users ORDER BY joined_at DESC")
            return await cursor.fetchall()

    async def get_today_users_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = DATE('now')")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_today_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT user_id, username, first_name, joined_at FROM users WHERE DATE(joined_at) = DATE('now') ORDER BY joined_at DESC")
            return await cursor.fetchall()

    # Referral Program Methods
    async def process_referral(self, new_user_id: int, referrer_id: int, points: int = 10) -> tuple[bool, str]:
        """Validate and reward referrer when a new user joins via link"""
        if new_user_id == referrer_id:
            return False, "Self referral not allowed"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Check if referrer exists
            cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
            referrer = await cursor.fetchone()
            if not referrer:
                return False, "Referrer does not exist"

            # Check if new user already has a recorded referral
            cursor = await db.execute("SELECT id FROM referrals WHERE referred_id = ?", (new_user_id,))
            existing_ref = await cursor.fetchone()
            if existing_ref:
                return False, "User already referred"

            # Record referral
            await db.execute("""
                INSERT INTO referrals (referrer_id, referred_id, points_rewarded)
                VALUES (?, ?, ?)
            """, (referrer_id, new_user_id, points))

            # Update new user referrer_id
            await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (referrer_id, new_user_id))

            # Reward referrer with points and increment referral count
            await db.execute("""
                UPDATE users 
                SET points = COALESCE(points, 0) + ?,
                    referral_count = COALESCE(referral_count, 0) + 1
                WHERE user_id = ?
            """, (points, referrer_id))

            await db.commit()
            return True, "Referral processed successfully"

    async def get_user_referral_stats(self, user_id: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT COALESCE(points, 0) as points, COALESCE(referral_count, 0) as referral_count FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                return {"points": row["points"], "referral_count": row["referral_count"]}
            return {"points": 0, "referral_count": 0}

    async def get_top_referrers(self, limit: int = 10):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT user_id, username, first_name, referral_count, points
                FROM users
                WHERE referral_count > 0
                ORDER BY referral_count DESC, points DESC
                LIMIT ?
            """, (limit,))
            return await cursor.fetchall()

    async def get_referral_stats_admin(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*), COALESCE(SUM(points_rewarded), 0) FROM referrals")
            row = await cursor.fetchone()
            total_refs = row[0] if row else 0
            total_points = row[1] if row else 0
            return {
                "total_referrals": total_refs,
                "total_points_awarded": total_points
            }

    # Admin Methods
    async def is_admin(self, user_id: int) -> bool:
        if user_id in ADMIN_IDS:
            return True
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return (await cursor.fetchone()) is not None

    async def add_admin(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def get_admins(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM admins")
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

    # Service Methods
    async def get_services_by_category(self, category_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, code, category_id, title, short_desc, full_desc, is_active FROM services WHERE category_id = ? AND is_active = 1",
                (category_id,)
            )
            return await cursor.fetchall()

    async def get_all_services_admin(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT id, code, category_id, title, is_active FROM services")
            return await cursor.fetchall()

    async def get_service_by_code(self, code: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, code, category_id, title, short_desc, full_desc, is_active FROM services WHERE code = ?",
                (code,)
            )
            return await cursor.fetchone()

    async def toggle_service_status(self, service_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE services SET is_active = 1 - is_active WHERE id = ?", (service_id,))
            await db.commit()

    # Leads Methods
    async def add_lead(self, user_id: int, username: str, first_name: str, service_code: str, service_title: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO leads (user_id, username, first_name, service_code, service_title)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, service_code, service_title))
            await db.commit()

    async def get_leads_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM leads")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_recent_leads(self, limit: int = 10):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT user_id, username, first_name, service_title, created_at
                FROM leads
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            return await cursor.fetchall()

    # Settings & Group Configuration
    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            await db.commit()

    async def get_setting(self, key: str, default: str = "") -> str:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else default

    async def get_admin_group_id(self) -> int | None:
        val = await self.get_setting("admin_group_id")
        if val and (val.startswith("-") or val.isdigit()):
            try:
                return int(val)
            except ValueError:
                pass
        if ADMIN_GROUP_ID:
            try:
                return int(ADMIN_GROUP_ID)
            except ValueError:
                pass
        return None

    async def set_admin_group_id(self, group_id: int):
        await self.set_setting("admin_group_id", str(group_id))

    async def get_admin_thread_id(self) -> int | None:
        val = await self.get_setting("admin_thread_id")
        if val and val.isdigit():
            try:
                return int(val)
            except ValueError:
                pass
        return None

    async def set_admin_thread_id(self, thread_id: int | None):
        if thread_id is not None:
            await self.set_setting("admin_thread_id", str(thread_id))
        else:
            await self.set_setting("admin_thread_id", "")

    # Message Mappings (2-way live chat relay)
    async def save_message_mapping(self, group_message_id: int, user_id: int, user_message_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO message_mappings (group_message_id, user_id, user_message_id)
                VALUES (?, ?, ?)
            """, (group_message_id, user_id, user_message_id))
            await db.commit()

    async def get_user_by_group_message_id(self, group_message_id: int) -> int | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM message_mappings WHERE group_message_id = ?", (group_message_id,))
            row = await cursor.fetchone()
            return row[0] if row else None

    # User Forum Topics (Individual Topic per User)
    async def get_user_thread_id(self, user_id: int) -> int | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT thread_id FROM user_topics WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return row[0] if row else None

    async def get_user_by_thread_id(self, thread_id: int) -> int | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM user_topics WHERE thread_id = ?", (thread_id,))
            row = await cursor.fetchone()
            return row[0] if row else None

    async def save_user_topic(self, user_id: int, thread_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_topics (user_id, thread_id)
                VALUES (?, ?)
            """, (user_id, thread_id))
            await db.commit()

    # Lead Tracking Methods
    async def add_lead(self, user_id: int, username: str, first_name: str, service_code: str, service_title: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO leads (user_id, username, first_name, service_code, service_title)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, service_code, service_title))
            await db.commit()

    async def get_recent_leads(self, limit: int = 10):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT user_id, username, first_name, service_title, created_at
                FROM leads
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return await cursor.fetchall()

    async def get_leads_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM leads")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_all_services_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT code, title, category_id, is_active FROM services")
            return await cursor.fetchall()
