from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ==================== USER KEYBOARDS ====================

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💎 Diamond Top-Up", callback_data="diamond_topup")],
        [InlineKeyboardButton("🎁 Special Offers", callback_data="special_offers")],
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [
            InlineKeyboardButton("👤 My Account", callback_data="my_account"),
            InlineKeyboardButton("📜 My Orders", callback_data="my_orders")
        ],
        [
            InlineKeyboardButton("🎟 Promo Code", callback_data="promo_code"),
            InlineKeyboardButton("🤝 Referral", callback_data="referral")
        ],
        [
            InlineKeyboardButton("📞 Support", callback_data="support"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def offers_keyboard(offers):
    keyboard = []
    for offer in offers:
        btn_text = f"{offer['button_name']} — ৳{offer['price']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"select_offer_{offer['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)


def confirm_order_keyboard(offer_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_order_{offer_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def deposit_method_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 bKash", callback_data="deposit_bkash")],
        [InlineKeyboardButton("💳 Nagad", callback_data="deposit_nagad")],
        [InlineKeyboardButton("💳 Rocket", callback_data="deposit_rocket")],
        [InlineKeyboardButton("💳 Binance", callback_data="deposit_binance")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)


# ==================== ADMIN KEYBOARDS ====================

def admin_dashboard_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎁 Manage Offers", callback_data="admin_offers")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("💵 Deposits", callback_data="admin_deposits")],
        [InlineKeyboardButton("📦 Orders", callback_data="admin_orders")],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🎟 Promo Codes", callback_data="admin_promo")
        ],
        [
            InlineKeyboardButton("🤝 Referral", callback_data="admin_referral"),
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"),
            InlineKeyboardButton("🛡️ Admin Management", callback_data="admin_management")
        ],
        [InlineKeyboardButton("🔙 Close", callback_data="close_dashboard")]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_offers_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Add Offer", callback_data="add_offer")],
        [InlineKeyboardButton("✏️ Edit Offer", callback_data="edit_offer")],
        [InlineKeyboardButton("🗑 Delete Offer", callback_data="delete_offer")],
        [InlineKeyboardButton("📋 All Offers", callback_data="all_offers")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_users_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔎 Search User", callback_data="search_user")],
        [InlineKeyboardButton("📋 All Users", callback_data="all_users")],
        [InlineKeyboardButton("💰 Add Balance", callback_data="add_balance")],
        [InlineKeyboardButton("➖ Remove Balance", callback_data="remove_balance")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user")],
        [InlineKeyboardButton("✅ Unban User", callback_data="unban_user")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_deposits_keyboard():
    keyboard = [
        [InlineKeyboardButton("📥 Pending Deposits", callback_data="pending_deposits")],
        [InlineKeyboardButton("✅ Approved Deposits", callback_data="approved_deposits")],
        [InlineKeyboardButton("❌ Rejected Deposits", callback_data="rejected_deposits")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_orders_keyboard():
    keyboard = [
        [InlineKeyboardButton("⏳ Pending Orders", callback_data="pending_orders")],
        [InlineKeyboardButton("✅ Completed Orders", callback_data="completed_orders")],
        [InlineKeyboardButton("❌ Cancelled Orders", callback_data="cancelled_orders")],
        [InlineKeyboardButton("🔎 Search Order", callback_data="search_order")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    return InlineKeyboardMarkup(keyboard)


def deposit_action_keyboard(deposit_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_deposit_{deposit_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_deposit_{deposit_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def order_action_keyboard(order_id):
    keyboard = [
        [
            InlineKeyboardButton("⚡ Process", callback_data=f"process_order_{order_id}"),
            InlineKeyboardButton("✅ Complete", callback_data=f"complete_order_{order_id}")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_order_admin_{order_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_keyboard(yes_data, no_data="cancel"):
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=yes_data),
            InlineKeyboardButton("❌ No", callback_data=no_data)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_admin_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_dashboard")]]
    return InlineKeyboardMarkup(keyboard)
