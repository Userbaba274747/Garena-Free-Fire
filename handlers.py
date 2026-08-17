from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from datetime import datetime
import database as db
from keyboards import *
from states import UserStates, AdminStates
from config import ADMINS


# ==================== HELPER ====================

async def is_user_banned(user_id):
    user = await db.get_user(user_id)
    return user and user["is_banned"] == 1


async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    maintenance = await db.get_setting("maintenance_mode")
    if maintenance == "True":
        text = "🔧 বট বর্তমানে মেইনটেনেন্স মোডে আছে। কিছুক্ষণ পর আবার চেষ্টা করুন।"
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return True
    return False


async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await db.is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("আপনার অনুমতি নেই!", show_alert=True)
        else:
            await update.message.reply_text("আপনার অনুমতি নেই!")
        return False
    return True


# ==================== USER HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referred_by = None

    # Referral check
    if context.args and context.args[0].startswith("ref"):
        try:
            referred_by = int(context.args[0].replace("ref", ""))
        except:
            pass

    await db.add_user(user.id, user.username, user.full_name, referred_by)

    if await is_user_banned(user.id):
        await update.message.reply_text("🚫 আপনাকে ব্যান করা হয়েছে। সাপোর্টে যোগাযোগ করুন।")
        return

    if await check_maintenance(update, context):
        return

    user_data = await db.get_user(user.id)
    balance = user_data["balance"] if user_data else 0

    text = (
        f"🎮 Welcome to Free Fire Top-Up Bot!\n\n"
        f"💰 Balance: ৳{balance:.2f}\n\n"
        f"🔥 Choose an option below:"
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_user_banned(query.from_user.id):
        await query.edit_message_text("🚫 আপনাকে ব্যান করা হয়েছে।")
        return

    if await check_maintenance(update, context):
        return

    user_data = await db.get_user(query.from_user.id)
    balance = user_data["balance"] if user_data else 0

    text = (
        f"🎮 Welcome to Free Fire Top-Up Bot!\n\n"
        f"💰 Balance: ৳{balance:.2f}\n\n"
        f"🔥 Choose an option below:"
    )
    await query.edit_message_text(text, reply_markup=main_menu_keyboard())


# ---------- Diamond Top-Up ----------
async def diamond_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_user_banned(query.from_user.id) or await check_maintenance(update, context):
        return

    offers = await db.get_all_offers(active_only=True)
    if not offers:
        await query.edit_message_text(
            "😔 এখন কোনো অফার নেই।",
            reply_markup=back_to_main_keyboard()
        )
        return

    text = "💎 FREE FIRE DIAMOND OFFERS\n\n"
    for offer in offers:
        text += f"💎 {offer['name']}\n💰 Price: ৳{offer['price']}\n\n"

    await query.edit_message_text(text, reply_markup=offers_keyboard(offers))


async def select_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offer_id = int(query.data.split("_")[-1])
    offer = await db.get_offer(offer_id)

    if not offer or offer["is_active"] == 0:
        await query.edit_message_text("এই অফারটি আর নেই।", reply_markup=back_to_main_keyboard())
        return

    context.user_data["selected_offer"] = offer_id

    text = (
        f"💎 {offer['name']}\n\n"
        f"💰 Price: ৳{offer['price']}\n"
        f"⚡ Delivery: {offer['delivery_time']}\n\n"
        f"Please enter your Free Fire UID:"
    )
    await query.edit_message_text(text)
    return UserStates.WAITING_UID


async def receive_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    offer_id = context.user_data.get("selected_offer")
    offer = await db.get_offer(offer_id)

    if not offer:
        await update.message.reply_text("অফার পাওয়া যায়নি।", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    user = await db.get_user(update.effective_user.id)
    if user["balance"] < offer["price"]:
        await update.message.reply_text(
            f"❌ আপনার ব্যালেন্স অপর্যাপ্ত!\n"
            f"প্রয়োজন: ৳{offer['price']}\n"
            f"আপনার ব্যালেন্স: ৳{user['balance']:.2f}\n\n"
            f"আগে Deposit করুন।",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

    context.user_data["uid"] = uid

    text = (
        f"📦 Order Confirmation\n\n"
        f"💎 {offer['name']}\n"
        f"💰 Price: ৳{offer['price']}\n"
        f"🆔 UID: {uid}\n"
        f"⚡ Delivery: {offer['delivery_time']}\n\n"
        f"Confirm করে Order করবেন?"
    )
    await update.message.reply_text(text, reply_markup=confirm_order_keyboard(offer_id))
    return ConversationHandler.END


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offer_id = int(query.data.split("_")[-1])
    offer = await db.get_offer(offer_id)
    uid = context.user_data.get("uid")
    user_id = query.from_user.id

    user = await db.get_user(user_id)
    if user["balance"] < offer["price"]:
        await query.edit_message_text("❌ ব্যালেন্স অপর্যাপ্ত!", reply_markup=back_to_main_keyboard())
        return

    # Balance কাটা
    await db.update_balance(user_id, -offer["price"])

    # Order তৈরি
    order_id = await db.create_order(
        user_id, offer_id, offer["name"], offer["diamonds"], offer["price"], uid
    )

    text = (
        f"✅ Order Created Successfully!\n\n"
        f"📦 Order ID: `{order_id}`\n"
        f"💎 {offer['name']}\n"
        f"🆔 UID: {uid}\n"
        f"💰 Amount: ৳{offer['price']}\n"
        f"⏳ Status: Pending\n\n"
        f"অ্যাডমিন শীঘ্রই প্রসেস করবে।"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())

    # Admin কে নোটিফিকেশন (ঐচ্ছিক)
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(
                admin_id,
                f"📦 New Order!\n\nOrder: {order_id}\nUser: {user_id}\nProduct: {offer['name']}\nUID: {uid}"
            )
        except:
            pass


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Order Cancelled.", reply_markup=back_to_main_keyboard())


# ---------- Deposit ----------
async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_user_banned(query.from_user.id) or await check_maintenance(update, context):
        return

    text = "💰 DEPOSIT\n\nSelect Payment Method:"
    await query.edit_message_text(text, reply_markup=deposit_method_keyboard())


async def deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    method = query.data.split("_")[1]  # bkash / nagad / rocket / binance
    context.user_data["deposit_method"] = method.capitalize()

    await query.edit_message_text("💰 Deposit Amount লিখুন (শুধু সংখ্যা):")
    return UserStates.WAITING_DEPOSIT_AMOUNT


async def receive_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return UserStates.WAITING_DEPOSIT_AMOUNT

    min_deposit = float(await db.get_setting("min_deposit") or 100)
    if amount < min_deposit:
        await update.message.reply_text(f"সর্বনিম্ন Deposit ৳{min_deposit}")
        return UserStates.WAITING_DEPOSIT_AMOUNT

    context.user_data["deposit_amount"] = amount
    method = context.user_data["deposit_method"]

    if method == "Bkash":
        number = await db.get_setting("bkash_number")
    elif method == "Nagad":
        number = await db.get_setting("nagad_number")
    elif method == "Rocket":
        number = await db.get_setting("rocket_number")
    else:
        number = await db.get_setting("binance_address")

    text = (
        f"💰 Deposit Amount: ৳{amount}\n\n"
        f"Send payment to:\n"
        f"📱 {method}: `{number}`\n\n"
        f"Then enter Transaction ID:"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return UserStates.WAITING_TRX_ID


async def receive_trx_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trx_id = update.message.text.strip()
    user_id = update.effective_user.id
    amount = context.user_data["deposit_amount"]
    method = context.user_data["deposit_method"]

    success = await db.create_deposit(user_id, amount, method, trx_id)
    if not success:
        await update.message.reply_text(
            "❌ এই Transaction ID আগে ব্যবহার করা হয়েছে!",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Deposit Request পাঠানো হয়েছে!\nঅ্যাডমিন Approve করলে Balance যোগ হবে।",
        reply_markup=main_menu_keyboard()
    )

    # Admin Notification
    for admin_id in ADMINS:
        try:
            deposits = await db.get_pending_deposits()
            dep = deposits[0] if deposits else None
            if dep:
                text = (
                    f"💵 NEW DEPOSIT REQUEST\n\n"
                    f"👤 User: @{update.effective_user.username or 'N/A'}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💰 Amount: ৳{amount}\n"
                    f"💳 Method: {method}\n"
                    f"🧾 TxID: `{trx_id}`"
                )
                await context.bot.send_message(
                    admin_id, text, parse_mode="Markdown",
                    reply_markup=deposit_action_keyboard(dep["id"])
                )
        except:
            pass

    return ConversationHandler.END


# ---------- My Account ----------
async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = await db.get_user(query.from_user.id)
    text = (
        f"👤 MY ACCOUNT\n\n"
        f"👤 Name: {user['full_name']}\n"
        f"🆔 ID: {user['user_id']}\n"
        f"🔗 Username: @{user['username'] or 'N/A'}\n\n"
        f"💰 Balance: ৳{user['balance']:.2f}\n"
        f"💵 Total Deposited: ৳{user['total_deposited']:.2f}\n"
        f"💎 Total Spent: ৳{user['total_spent']:.2f}\n"
        f"📅 Joined: {user['joined_at'][:10]}"
    )
    await query.edit_message_text(text, reply_markup=back_to_main_keyboard())


# ---------- My Orders ----------
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    orders = await db.get_user_orders(query.from_user.id)
    if not orders:
        await query.edit_message_text("আপনার কোনো Order নেই।", reply_markup=back_to_main_keyboard())
        return

    text = "📜 MY ORDERS\n\n"
    for order in orders[:10]:
        text += (
            f"📦 `{order['order_id']}`\n"
            f"💎 {order['offer_name']}\n"
            f"💰 ৳{order['price']} | {order['status']}\n\n"
        )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())


# ---------- Promo Code ----------
async def promo_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎟 Promo Code লিখুন:")
    return UserStates.WAITING_PROMO_CODE


async def receive_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()
    promo = await db.get_promo(code)

    if not promo:
        await update.message.reply_text("❌ অবৈধ Promo Code!", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    if promo["used_count"] >= promo["max_uses"]:
        await update.message.reply_text("❌ এই কোডের ব্যবহার শেষ!", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    await update.message.reply_text(
        f"✅ Promo Applied!\nDiscount: ৳{promo['discount']}\n"
        f"(পরবর্তী পারচেজে কাটা হবে)",
        reply_markup=main_menu_keyboard()
    )
    context.user_data["promo_discount"] = promo["discount"]
    return ConversationHandler.END


# ---------- Referral ----------
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bot_info = await context.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref{user_id}"

    text = (
        f"🤝 REFERRAL\n\n"
        f"🔗 Your Link:\n`{link}`\n\n"
        f"বন্ধুদের শেয়ার করুন এবং রিওয়ার্ড পান!"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())


# ---------- Support & Help ----------
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    support_user = await db.get_setting("support_username") or "@Support"
    await query.edit_message_text(
        f"📞 Support: {support_user}\n\nযেকোনো সমস্যায় যোগাযোগ করুন।",
        reply_markup=back_to_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "ℹ️ HELP\n\n"
        "1️⃣ আগে Deposit করে Balance যোগ করুন\n"
        "2️⃣ Diamond Top-Up থেকে অফার সিলেক্ট করুন\n"
        "3️⃣ Free Fire UID দিন\n"
        "4️⃣ Confirm করুন\n\n"
        "কোনো সমস্যা হলে Support এ যোগাযোগ করুন।"
    )
    await query.edit_message_text(text, reply_markup=back_to_main_keyboard())


# ==================== ADMIN HANDLERS ====================

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return

    stats = await db.get_stats()
    text = (
        f"👑 ADMIN DASHBOARD\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"🟢 Active Users: {stats['active_users']}\n"
        f"🚫 Banned Users: {stats['banned_users']}\n"
        f"📦 Total Orders: {stats['total_orders']}\n"
        f"⏳ Pending Orders: {stats['pending_orders']}\n"
        f"💵 Total Deposits: ৳{stats['total_deposits']:.2f}\n"
        f"💎 Total Sales: ৳{stats['total_sales']:.2f}\n\n"
        f"Choose an option:"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=admin_dashboard_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=admin_dashboard_keyboard())


async def admin_offers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("🎁 Manage Offers", reply_markup=admin_offers_keyboard())


async def admin_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("👥 Users Management", reply_markup=admin_users_keyboard())


async def admin_deposits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("💵 Deposits", reply_markup=admin_deposits_keyboard())


async def admin_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("📦 Orders", reply_markup=admin_orders_keyboard())


# ---------- Pending Deposits ----------
async def pending_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    deposits = await db.get_pending_deposits()
    if not deposits:
        await query.edit_message_text("কোনো Pending Deposit নেই।", reply_markup=back_to_admin_keyboard())
        return

    for dep in deposits[:5]:
        user = await db.get_user(dep["user_id"])
        text = (
            f"💵 DEPOSIT REQUEST\n\n"
            f"👤 User: @{user['username'] or 'N/A'}\n"
            f"🆔 ID: {dep['user_id']}\n"
            f"💰 Amount: ৳{dep['amount']}\n"
            f"💳 Method: {dep['method']}\n"
            f"🧾 TxID: `{dep['trx_id']}`"
        )
        await context.bot.send_message(
            query.from_user.id, text, parse_mode="Markdown",
            reply_markup=deposit_action_keyboard(dep["id"])
        )
    await query.edit_message_text("Pending Deposits পাঠানো হয়েছে।", reply_markup=back_to_admin_keyboard())


async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    deposit_id = int(query.data.split("_")[-1])
    dep = await db.get_deposit(deposit_id)
    if not dep or dep["status"] != "Pending":
        await query.edit_message_text("ইতিমধ্যে প্রসেস করা হয়েছে।")
        return

    await db.update_deposit_status(deposit_id, "Approved")
    await db.update_balance(dep["user_id"], dep["amount"])

    await query.edit_message_text(f"✅ Deposit Approved! ৳{dep['amount']} যোগ করা হয়েছে।")

    try:
        await context.bot.send_message(
            dep["user_id"],
            f"✅ আপনার Deposit Approve হয়েছে!\n💰 ৳{dep['amount']} Balance-এ যোগ করা হয়েছে।"
        )
    except:
        pass


async def reject_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    deposit_id = int(query.data.split("_")[-1])
    dep = await db.get_deposit(deposit_id)
    if not dep or dep["status"] != "Pending":
        await query.edit_message_text("ইতিমধ্যে প্রসেস করা হয়েছে।")
        return

    await db.update_deposit_status(deposit_id, "Rejected")
    await query.edit_message_text("❌ Deposit Rejected.")

    try:
        await context.bot.send_message(dep["user_id"], "❌ আপনার Deposit Request Reject করা হয়েছে।")
    except:
        pass


# ---------- Orders Admin ----------
async def pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    orders = await db.get_orders_by_status("Pending")
    if not orders:
        await query.edit_message_text("কোনো Pending Order নেই।", reply_markup=back_to_admin_keyboard())
        return

    for order in orders[:5]:
        text = (
            f"📦 ORDER `{order['order_id']}`\n\n"
            f"👤 User ID: {order['user_id']}\n"
            f"💎 {order['offer_name']}\n"
            f"🆔 UID: {order['uid']}\n"
            f"💰 ৳{order['price']}\n"
            f"⏳ Status: Pending"
        )
        await context.bot.send_message(
            query.from_user.id, text, parse_mode="Markdown",
            reply_markup=order_action_keyboard(order["order_id"])
        )
    await query.edit_message_text("Pending Orders পাঠানো হয়েছে।", reply_markup=back_to_admin_keyboard())


async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    order_id = query.data.split("_")[-1]
    order = await db.get_order(order_id)
    if not order:
        await query.edit_message_text("Order পাওয়া যায়নি।")
        return

    await db.update_order_status(order_id, "Completed")
    await query.edit_message_text(f"✅ Order `{order_id}` Completed!", parse_mode="Markdown")

    try:
        delivery_msg = await db.get_setting("delivery_message")
        await context.bot.send_message(
            order["user_id"],
            f"✅ আপনার Order সম্পন্ন হয়েছে!\n📦 Order ID: `{order_id}`\n\n{delivery_msg}",
            parse_mode="Markdown"
        )
    except:
        pass


# ---------- Statistics ----------
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    stats = await db.get_stats()
    text = (
        f"📊 BOT STATISTICS\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"🟢 Active: {stats['active_users']}\n"
        f"🚫 Banned: {stats['banned_users']}\n\n"
        f"💵 Total Deposit: ৳{stats['total_deposits']:.2f}\n"
        f"💎 Total Sales: ৳{stats['total_sales']:.2f}\n\n"
        f"📦 Orders: {stats['total_orders']}\n"
        f"✅ Completed: {stats['completed_orders']}\n"
        f"⏳ Pending: {stats['pending_orders']}"
    )
    await query.edit_message_text(text, reply_markup=back_to_admin_keyboard())


# ---------- Cancel Conversation ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("বাতিল করা হয়েছে।", reply_markup=main_menu_keyboard())
    return ConversationHandler.END
  # ==================== OFFER ADD (Conversation) ====================

async def add_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("🎁 নতুন অফারের নাম লিখুন:")
    return AdminStates.ADD_OFFER_NAME


async def add_offer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["offer_name"] = update.message.text.strip()
    await update.message.reply_text("💎 Diamond Amount লিখুন (শুধু সংখ্যা):")
    return AdminStates.ADD_OFFER_DIAMONDS


async def add_offer_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        diamonds = int(update.message.text.strip())
        context.user_data["offer_diamonds"] = diamonds
        await update.message.reply_text("💰 Price লিখুন (শুধু সংখ্যা):")
        return AdminStates.ADD_OFFER_PRICE
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_OFFER_DIAMONDS


async def add_offer_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.strip())
        context.user_data["offer_price"] = price
        await update.message.reply_text("🔘 Button Name লিখুন (উদাহরণ: 💎 Buy 310 Diamonds):")
        return AdminStates.ADD_OFFER_BUTTON
    except:
        await update.message.reply_text("সঠিক দাম লিখুন:")
        return AdminStates.ADD_OFFER_PRICE


async def add_offer_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["offer_button"] = update.message.text.strip()
    await update.message.reply_text("📝 Description লিখুন (না থাকলে 'skip' লিখুন):")
    return AdminStates.ADD_OFFER_DESCRIPTION


async def add_offer_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    if desc.lower() == "skip":
        desc = ""
    context.user_data["offer_description"] = desc
    await update.message.reply_text("⚡ Delivery Time লিখুন (উদাহরণ: 1-5 Minutes):")
    return AdminStates.ADD_OFFER_DELIVERY


async def add_offer_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delivery = update.message.text.strip()
    context.user_data["offer_delivery"] = delivery

    # Preview
    text = (
        f"🎁 NEW OFFER PREVIEW\n\n"
        f"💎 Name: {context.user_data['offer_name']}\n"
        f"💎 Diamonds: {context.user_data['offer_diamonds']}\n"
        f"💰 Price: ৳{context.user_data['offer_price']}\n"
        f"🔘 Button: {context.user_data['offer_button']}\n"
        f"📝 Description: {context.user_data['offer_description'] or 'N/A'}\n"
        f"⚡ Delivery: {delivery}\n\n"
        f"Save করতে চাও?"
    )
    keyboard = [
        [
            InlineKeyboardButton("✅ Save", callback_data="save_offer"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_offer")
        ]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def save_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offer_id = await db.add_offer(
        name=context.user_data["offer_name"],
        diamonds=context.user_data["offer_diamonds"],
        price=context.user_data["offer_price"],
        button_name=context.user_data["offer_button"],
        description=context.user_data.get("offer_description", ""),
        delivery_time=context.user_data["offer_delivery"]
    )

    await query.edit_message_text(f"✅ অফার সফলভাবে অ্যাড হয়েছে! (ID: {offer_id})")

    # নতুন অফার নোটিফিকেশন
    notify = await db.get_setting("new_offer_notification")
    if notify == "True":
        users = await db.get_all_users()
        text = (
            f"🎉 NEW OFFER AVAILABLE!\n\n"
            f"💎 {context.user_data['offer_name']}\n"
            f"💰 Only ৳{context.user_data['offer_price']}\n\n"
            f"🔥 Grab it now!"
        )
        for user in users:
            if user["is_banned"] == 0:
                try:
                    await context.bot.send_message(user["user_id"], text)
                except:
                    pass


async def cancel_add_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ অফার অ্যাড বাতিল করা হয়েছে।")


# ==================== BAN / UNBAN ====================

async def ban_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("🚫 ব্যান করতে User ID লিখুন:")
    return AdminStates.BAN_USER_ID


async def ban_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        context.user_data["ban_user_id"] = user_id
        await update.message.reply_text("Reason লিখুন (Spam / Fraud / Abuse / Other):")
        return AdminStates.BAN_REASON
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.BAN_USER_ID


async def ban_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text.strip()
    user_id = context.user_data["ban_user_id"]
    await db.ban_user(user_id, reason)

    await update.message.reply_text(f"✅ User `{user_id}` ব্যান করা হয়েছে।\nReason: {reason}", parse_mode="Markdown")
    return ConversationHandler.END


async def unban_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("✅ আনব্যান করতে User ID লিখুন:")
    return AdminStates.UNBAN_USER_ID


async def unban_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        await db.unban_user(user_id)
        await update.message.reply_text(f"✅ User `{user_id}` আনব্যান করা হয়েছে।", parse_mode="Markdown")
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.UNBAN_USER_ID
    return ConversationHandler.END


# ==================== ADD / REMOVE BALANCE ====================

async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("💰 Balance অ্যাড করতে User ID লিখুন:")
    return AdminStates.ADD_BALANCE_USER


async def add_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        context.user_data["balance_user_id"] = user_id
        await update.message.reply_text("কত টাকা অ্যাড করবেন?")
        return AdminStates.ADD_BALANCE_AMOUNT
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.ADD_BALANCE_USER


async def add_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        user_id = context.user_data["balance_user_id"]
        await db.update_balance(user_id, amount)
        await update.message.reply_text(f"✅ ৳{amount} অ্যাড করা হয়েছে User `{user_id}`-এ।", parse_mode="Markdown")

        try:
            await context.bot.send_message(user_id, f"💰 আপনার অ্যাকাউন্টে ৳{amount} যোগ করা হয়েছে।")
        except:
            pass
    except:
        await update.message.reply_text("সঠিক পরিমাণ লিখুন:")
        return AdminStates.ADD_BALANCE_AMOUNT
    return ConversationHandler.END


async def remove_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("➖ Balance কাটতে User ID লিখুন:")
    return AdminStates.REMOVE_BALANCE_USER


async def remove_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        context.user_data["balance_user_id"] = user_id
        await update.message.reply_text("কত টাকা কাটবেন?")
        return AdminStates.REMOVE_BALANCE_AMOUNT
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.REMOVE_BALANCE_USER


async def remove_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        user_id = context.user_data["balance_user_id"]
        await db.update_balance(user_id, -amount)
        await update.message.reply_text(f"✅ ৳{amount} কাটা হয়েছে User `{user_id}` থেকে।", parse_mode="Markdown")
    except:
        await update.message.reply_text("সঠিক পরিমাণ লিখুন:")
        return AdminStates.REMOVE_BALANCE_AMOUNT
    return ConversationHandler.END


# ==================== BROADCAST ====================

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("📢 Broadcast মেসেজ লিখুন:")
    return AdminStates.BROADCAST_MESSAGE


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcast_text"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("✅ Send to All Users", callback_data="broadcast_all")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
    ]
    await update.message.reply_text(
        f"Preview:\n\n{context.user_data['broadcast_text']}\n\nপাঠাবেন?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = context.user_data.get("broadcast_text")
    users = await db.get_all_users()
    success = 0
    fail = 0

    await query.edit_message_text("📤 Broadcast শুরু হয়েছে...")

    for user in users:
        if user["is_banned"] == 0:
            try:
                await context.bot.send_message(user["user_id"], text)
                success += 1
            except:
                fail += 1

    await context.bot.send_message(
        query.from_user.id,
        f"✅ Broadcast শেষ!\nসফল: {success}\nব্যর্থ: {fail}"
    )


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Broadcast বাতিল করা হয়েছে।")


# ==================== ALL OFFERS (Admin) ====================

async def all_offers_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    offers = await db.get_all_offers(active_only=False)
    if not offers:
        await query.edit_message_text("কোনো অফার নেই।", reply_markup=back_to_admin_keyboard())
        return

    text = "📋 ALL OFFERS\n\n"
    for offer in offers:
        status = "🟢 Active" if offer["is_active"] else "🔴 Disabled"
        text += f"ID: {offer['id']} | {offer['name']} | ৳{offer['price']} | {status}\n"

    await query.edit_message_text(text, reply_markup=back_to_admin_keyboard())
  # ==================== DELETE OFFER ====================

async def delete_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    offers = await db.get_all_offers(active_only=False)
    if not offers:
        await query.edit_message_text("কোনো অফার নেই।", reply_markup=back_to_admin_keyboard())
        return

    keyboard = []
    for offer in offers:
        keyboard.append([InlineKeyboardButton(
            f"{offer['name']} - ৳{offer['price']}", 
            callback_data=f"delete_offer_{offer['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_offers")])
    
    await query.edit_message_text("🗑 কোন অফার ডিলিট করবেন?", reply_markup=InlineKeyboardMarkup(keyboard))


async def delete_offer_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    offer_id = int(query.data.split("_")[-1])
    offer = await db.get_offer(offer_id)
    
    if offer:
        await db.delete_offer(offer_id)
        await query.edit_message_text(f"✅ অফার ডিলিট করা হয়েছে: {offer['name']}")
    else:
        await query.edit_message_text("অফার পাওয়া যায়নি।")


# ==================== EDIT OFFER (Basic) ====================

async def edit_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    offers = await db.get_all_offers(active_only=False)
    if not offers:
        await query.edit_message_text("কোনো অফার নেই।", reply_markup=back_to_admin_keyboard())
        return

    keyboard = []
    for offer in offers:
        keyboard.append([InlineKeyboardButton(
            f"{offer['name']} - ৳{offer['price']}", 
            callback_data=f"edit_select_{offer['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_offers")])
    
    await query.edit_message_text("✏️ কোন অফার এডিট করবেন?", reply_markup=InlineKeyboardMarkup(keyboard))


async def edit_offer_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    offer_id = int(query.data.split("_")[-1])
    context.user_data["edit_offer_id"] = offer_id
    offer = await db.get_offer(offer_id)

    keyboard = [
        [InlineKeyboardButton("✏️ Edit Name", callback_data="edit_field_name")],
        [InlineKeyboardButton("💎 Edit Diamonds", callback_data="edit_field_diamonds")],
        [InlineKeyboardButton("💰 Edit Price", callback_data="edit_field_price")],
        [InlineKeyboardButton("🔘 Edit Button Name", callback_data="edit_field_button")],
        [InlineKeyboardButton("📝 Edit Description", callback_data="edit_field_description")],
        [InlineKeyboardButton("⚡ Edit Delivery Time", callback_data="edit_field_delivery")],
        [InlineKeyboardButton("🟢 Enable / 🔴 Disable", callback_data="edit_field_status")],
        [InlineKeyboardButton("🔙 Back", callback_data="edit_offer")]
    ]
    
    text = (
        f"✏️ Editing: {offer['name']}\n\n"
        f"💎 Diamonds: {offer['diamonds']}\n"
        f"💰 Price: ৳{offer['price']}\n"
        f"🔘 Button: {offer['button_name']}\n"
        f"⚡ Delivery: {offer['delivery_time']}\n"
        f"Status: {'🟢 Active' if offer['is_active'] else '🔴 Disabled'}"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def edit_field_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    field = query.data.replace("edit_field_", "")
    context.user_data["edit_field"] = field

    if field == "status":
        offer_id = context.user_data["edit_offer_id"]
        offer = await db.get_offer(offer_id)
        new_status = 0 if offer["is_active"] == 1 else 1
        await db.update_offer(offer_id, is_active=new_status)
        status_text = "Enabled" if new_status == 1 else "Disabled"
        await query.edit_message_text(f"✅ Offer {status_text} করা হয়েছে!")
        return

    await query.edit_message_text(f"নতুন মান লিখুন ({field}):")
    return AdminStates.EDIT_OFFER_VALUE


async def edit_offer_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    offer_id = context.user_data["edit_offer_id"]
    field = context.user_data["edit_field"]

    try:
        if field == "diamonds":
            value = int(value)
        elif field == "price":
            value = float(value)
        
        await db.update_offer(offer_id, **{field if field != "button" else "button_name": value})
        await update.message.reply_text(f"✅ {field} আপডেট করা হয়েছে!")
    except Exception as e:
        await update.message.reply_text(f"এরর: {e}")
    
    return ConversationHandler.END


# ==================== PROMO CODE CREATE ====================

async def add_promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("🎟 Promo Code লিখুন (উদাহরণ: FF50):")
    return AdminStates.ADD_PROMO_CODE


async def add_promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["promo_code"] = update.message.text.strip().upper()
    await update.message.reply_text("Discount Amount লিখুন (৳):")
    return AdminStates.ADD_PROMO_DISCOUNT


async def add_promo_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["promo_discount"] = float(update.message.text.strip())
        await update.message.reply_text("Maximum Uses লিখুন:")
        return AdminStates.ADD_PROMO_USES
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_PROMO_DISCOUNT


async def add_promo_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["promo_uses"] = int(update.message.text.strip())
        await update.message.reply_text("Minimum Purchase Amount লিখুন:")
        return AdminStates.ADD_PROMO_MIN
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_PROMO_USES


async def add_promo_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["promo_min"] = float(update.message.text.strip())
        await update.message.reply_text("Expiry Date লিখুন (উদাহরণ: 2026-09-30):")
        return AdminStates.ADD_PROMO_EXPIRY
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_PROMO_MIN


async def add_promo_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expiry = update.message.text.strip()
    await db.add_promo(
        code=context.user_data["promo_code"],
        discount=context.user_data["promo_discount"],
        max_uses=context.user_data["promo_uses"],
        min_purchase=context.user_data["promo_min"],
        expiry_date=expiry
    )
    await update.message.reply_text(
        f"✅ Promo Code তৈরি হয়েছে!\n\n"
        f"Code: `{context.user_data['promo_code']}`\n"
        f"Discount: ৳{context.user_data['promo_discount']}\n"
        f"Uses: {context.user_data['promo_uses']}\n"
        f"Min Purchase: ৳{context.user_data['promo_min']}\n"
        f"Expiry: {expiry}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ==================== SETTINGS ====================

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    bkash = await db.get_setting("bkash_number")
    nagad = await db.get_setting("nagad_number")
    rocket = await db.get_setting("rocket_number")
    binance = await db.get_setting("binance_address")
    min_dep = await db.get_setting("min_deposit")
    ref_reward = await db.get_setting("referral_reward")
    maintenance = await db.get_setting("maintenance_mode")
    support = await db.get_setting("support_username")

    text = (
        f"⚙️ SETTINGS\n\n"
        f"💳 bKash: `{bkash}`\n"
        f"💳 Nagad: `{nagad}`\n"
        f"💳 Rocket: `{rocket}`\n"
        f"💳 Binance: `{binance}`\n\n"
        f"💰 Min Deposit: ৳{min_dep}\n"
        f"🤝 Referral Reward: ৳{ref_reward}\n"
        f"🔧 Maintenance: {maintenance}\n"
        f"📞 Support: {support}"
    )

    keyboard = [
        [InlineKeyboardButton("✏️ Edit bKash", callback_data="set_bkash_number")],
        [InlineKeyboardButton("✏️ Edit Nagad", callback_data="set_nagad_number")],
        [InlineKeyboardButton("✏️ Edit Rocket", callback_data="set_rocket_number")],
        [InlineKeyboardButton("✏️ Edit Binance", callback_data="set_binance_address")],
        [InlineKeyboardButton("✏️ Min Deposit", callback_data="set_min_deposit")],
        [InlineKeyboardButton("✏️ Referral Reward", callback_data="set_referral_reward")],
        [InlineKeyboardButton("🔧 Toggle Maintenance", callback_data="toggle_maintenance")],
        [InlineKeyboardButton("📞 Edit Support", callback_data="set_support_username")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def edit_setting_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    key = query.data.replace("set_", "")
    context.user_data["edit_setting_key"] = key
    await query.edit_message_text(f"নতুন মান লিখুন ({key}):")
    return AdminStates.EDIT_SETTING_VALUE


async def edit_setting_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    key = context.user_data["edit_setting_key"]
    await db.set_setting(key, value)
    await update.message.reply_text(f"✅ {key} আপডেট করা হয়েছে!")
    return ConversationHandler.END


async def toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current = await db.get_setting("maintenance_mode")
    new_value = "False" if current == "True" else "True"
    await db.set_setting("maintenance_mode", new_value)
    
    status = "চালু" if new_value == "True" else "বন্ধ"
    await query.edit_message_text(f"🔧 Maintenance Mode {status} করা হয়েছে!")


# ==================== ADMIN MANAGEMENT ====================

async def admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    keyboard = [
        [InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("➖ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    await query.edit_message_text("🛡️ Admin Management", reply_markup=InlineKeyboardMarkup(keyboard))


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("নতুন Admin-এর User ID লিখুন:")
    return AdminStates.ADD_ADMIN_ID


async def add_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        await db.add_admin(user_id)
        await update.message.reply_text(f"✅ User `{user_id}` Admin করা হয়েছে।", parse_mode="Markdown")
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.ADD_ADMIN_ID
    return ConversationHandler.END


async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("কোন Admin রিমুভ করবেন? User ID লিখুন:")
    return AdminStates.REMOVE_ADMIN_ID


async def remove_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        await db.remove_admin(user_id)
        await update.message.reply_text(f"✅ User `{user_id}` Admin থেকে রিমুভ করা হয়েছে।", parse_mode="Markdown")
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.REMOVE_ADMIN_ID
    return ConversationHandler.END


# ==================== CLOSE DASHBOARD ====================

async def close_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Dashboard বন্ধ করা হয়েছে।")
  # ==================== SEARCH USER + USER DETAILS ====================

async def search_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("🔎 User ID লিখুন:")
    return AdminStates.SEARCH_USER


async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        user = await db.get_user(user_id)

        if not user:
            await update.message.reply_text("User পাওয়া যায়নি।")
            return ConversationHandler.END

        text = (
            f"👥 USER DETAILS\n\n"
            f"👤 Name: {user['full_name']}\n"
            f"🆔 ID: {user['user_id']}\n"
            f"🔗 Username: @{user['username'] or 'N/A'}\n\n"
            f"💰 Balance: ৳{user['balance']:.2f}\n"
            f"💵 Total Deposited: ৳{user['total_deposited']:.2f}\n"
            f"💎 Total Spent: ৳{user['total_spent']:.2f}\n"
            f"📅 Joined: {user['joined_at'][:10]}\n"
            f"🟢 Status: {'Banned' if user['is_banned'] else 'Active'}"
        )

        keyboard = [
            [
                InlineKeyboardButton("💰 Add Balance", callback_data=f"quick_add_{user_id}"),
                InlineKeyboardButton("➖ Remove Balance", callback_data=f"quick_remove_{user_id}")
            ],
            [
                InlineKeyboardButton("🚫 Ban", callback_data=f"quick_ban_{user_id}"),
                InlineKeyboardButton("✅ Unban", callback_data=f"quick_unban_{user_id}")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_users")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.SEARCH_USER

    return ConversationHandler.END


# ==================== ORDER ACTIONS (Process / Cancel) ====================

async def process_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    order_id = query.data.split("_")[-1]
    await db.update_order_status(order_id, "Processing")
    await query.edit_message_text(f"⚡ Order `{order_id}` Processing করা হয়েছে।", parse_mode="Markdown")


async def cancel_order_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    order_id = query.data.split("_")[-1]
    order = await db.get_order(order_id)

    if order and order["status"] == "Pending":
        # Balance ফেরত দেওয়া
        await db.update_balance(order["user_id"], order["price"])
        await db.update_order_status(order_id, "Cancelled")

        await query.edit_message_text(f"❌ Order `{order_id}` Cancel করা হয়েছে এবং টাকা ফেরত দেওয়া হয়েছে।", parse_mode="Markdown")

        try:
            await context.bot.send_message(
                order["user_id"],
                f"❌ আপনার Order `{order_id}` Cancel করা হয়েছে।\n💰 ৳{order['price']} Balance-এ ফেরত দেওয়া হয়েছে।"
            )
        except:
            pass
    else:
        await query.edit_message_text("Order Cancel করা যায়নি।")


# ==================== SPECIAL OFFERS (User) ====================

async def special_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # আপাতত Diamond Top-Up এর মতোই কাজ করবে
    await diamond_topup(update, context)


# ==================== QUICK ACTIONS FROM USER DETAILS ====================

async def quick_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    await db.ban_user(user_id, "Banned by Admin")
    await query.edit_message_text(f"🚫 User `{user_id}` ব্যান করা হয়েছে।", parse_mode="Markdown")


async def quick_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    await db.unban_user(user_id)
    await query.edit_message_text(f"✅ User `{user_id}` আনব্যান করা হয়েছে।", parse_mode="Markdown")
  # ==================== ALL USERS ====================

async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    users = await db.get_all_users()
    if not users:
        await query.edit_message_text("কোনো ইউজার নেই।", reply_markup=back_to_admin_keyboard())
        return

    text = f"👥 ALL USERS (Total: {len(users)})\n\n"
    for user in users[:30]:  # প্রথমে ৩০ জন দেখাবে
        status = "🚫" if user["is_banned"] else "🟢"
        text += f"{status} `{user['user_id']}` - @{user['username'] or 'N/A'} | ৳{user['balance']:.0f}\n"

    if len(users) > 30:
        text += f"\n... এবং আরও {len(users)-30} জন"

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_admin_keyboard())


# ==================== APPROVED / REJECTED DEPOSITS ====================

async def approved_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    async with db.aiosqlite.connect(db.DB_NAME) as conn:
        conn.row_factory = db.aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM deposits WHERE status = 'Approved' ORDER BY id DESC LIMIT 15"
        )
        deposits = await cursor.fetchall()

    if not deposits:
        await query.edit_message_text("কোনো Approved Deposit নেই।", reply_markup=back_to_admin_keyboard())
        return

    text = "✅ APPROVED DEPOSITS\n\n"
    for dep in deposits:
        text += f"🆔 {dep['user_id']} | ৳{dep['amount']} | {dep['method']} | `{dep['trx_id']}`\n"

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_admin_keyboard())


async def rejected_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    async with db.aiosqlite.connect(db.DB_NAME) as conn:
        conn.row_factory = db.aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM deposits WHERE status = 'Rejected' ORDER BY id DESC LIMIT 15"
        )
        deposits = await cursor.fetchall()

    if not deposits:
        await query.edit_message_text("কোনো Rejected Deposit নেই।", reply_markup=back_to_admin_keyboard())
        return

    text = "❌ REJECTED DEPOSITS\n\n"
    for dep in deposits:
        text += f"🆔 {dep['user_id']} | ৳{dep['amount']} | {dep['method']} | `{dep['trx_id']}`\n"

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_admin_keyboard())


# ==================== COMPLETED / CANCELLED ORDERS ====================

async def completed_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    orders = await db.get_orders_by_status("Completed")
    if not orders:
        await query.edit_message_text("কোনো Completed Order নেই।", reply_markup=back_to_admin_keyboard())
        return

    text = "✅ COMPLETED ORDERS\n\n"
    for order in orders[:15]:
        text += f"`{order['order_id']}` | {order['offer_name']} | ৳{order['price']}\n"

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_admin_keyboard())


async def cancelled_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    orders = await db.get_orders_by_status("Cancelled")
    if not orders:
        await query.edit_message_text("কোনো Cancelled Order নেই।", reply_markup=back_to_admin_keyboard())
        return

    text = "❌ CANCELLED ORDERS\n\n"
    for order in orders[:15]:
        text += f"`{order['order_id']}` | {order['offer_name']} | ৳{order['price']}\n"

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_admin_keyboard())


# ==================== SEARCH ORDER ====================

async def search_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END

    await query.edit_message_text("🔎 Order ID লিখুন:")
    return AdminStates.SEARCH_ORDER


async def search_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = update.message.text.strip()
    order = await db.get_order(order_id)

    if not order:
        await update.message.reply_text("Order পাওয়া যায়নি।")
        return ConversationHandler.END

    text = (
        f"📦 ORDER DETAILS\n\n"
        f"Order ID: `{order['order_id']}`\n"
        f"User ID: {order['user_id']}\n"
        f"Product: {order['offer_name']}\n"
        f"UID: {order['uid']}\n"
        f"Amount: ৳{order['price']}\n"
        f"Status: {order['status']}\n"
        f"Time: {order['created_at'][:16]}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return ConversationHandler.END


# ==================== REFERRAL REWARD (Basic) ====================

async def give_referral_reward(referrer_id, amount=None):
    """নতুন ইউজার জয়েন করলে বা ডিপোজিট করলে রিওয়ার্ড দেওয়ার জন্য"""
    if amount is None:
        amount = float(await db.get_setting("referral_reward") or 20)
    
    await db.update_balance(referrer_id, amount)
    # চাইলে এখানে নোটিফিকেশন পাঠানো যায়


# ==================== CANCEL EVERYTHING ====================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "❌ বাতিল করা হয়েছে।",
            reply_markup=main_menu_keyboard()
        )
    return ConversationHandler.END
