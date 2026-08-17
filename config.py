import os
from dotenv import load_dotenv

load_dotenv()

# বট টোকেন (এখানে নিজের টোকেন দাও)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8880691679:AAG34KzlxfjLwMFPJPLu4w0t-h1Pzhdh6OA")

# মেইন অ্যাডমিন আইডি (নিজের Telegram ID দাও)
ADMINS = [8136997138]  # একাধিক অ্যাডমিন থাকলে কমা দিয়ে যোগ করো

# ডাটাবেস ফাইল
DB_NAME = "freefire_bot.db"

# ডিফল্ট সেটিংস
DEFAULT_SETTINGS = {
    "bkash_number": "01XXXXXXXXX",
    "nagad_number": "01XXXXXXXXX",
    "rocket_number": "01XXXXXXXXX",
    "binance_address": "YourBinanceAddress",
    "min_deposit": 100,
    "min_purchase": 50,
    "referral_reward": 20,
    "new_offer_notification": True,
    "maintenance_mode": False,
    "support_username": "@YourSupport",
    "terms": "আমাদের টার্মস এন্ড কন্ডিশনস এখানে লিখুন।",
    "delivery_message": "আপনার অর্ডার সফলভাবে সম্পন্ন হয়েছে! ১-৫ মিনিটের মধ্যে ডায়মন্ড পেয়ে যাবেন।"
}
