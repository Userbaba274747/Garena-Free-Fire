import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

from config import BOT_TOKEN
import database as db
from states import UserStates, AdminStates
import handlers as h

# লগিং সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """বট স্টার্ট হওয়ার সময় ডাটাবেস ইনিশিয়ালাইজ"""
    await db.init_db()
    logger.info("Database initialized successfully!")


def main():
    # অ্যাপ্লিকেশন তৈরি
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # ==================== USER CONVERSATION HANDLERS ====================

    # Deposit Conversation
    deposit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.deposit_method, pattern="^deposit_(bkash|nagad|rocket|binance)$")],
        states={
            UserStates.WAITING_DEPOSIT_AMOUNT: [
                MessageHandler(filters.TEXT & \~filters.COMMAND, h.receive_deposit_amount)
            ],
            UserStates.WAITING_TRX_ID: [
                MessageHandler(filters.TEXT & \~filters.COMMAND, h.receive_trx_id)
            ],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Order UID Conversation
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.select_offer, pattern="^select_offer_")],
        states={
            UserStates.WAITING_UID: [
                MessageHandler(filters.TEXT & \~filters.COMMAND, h.receive_uid)
            ],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Promo Code Conversation
    promo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.promo_code_start, pattern="^promo_code$")],
        states={
            UserStates.WAITING_PROMO_CODE: [
                MessageHandler(filters.TEXT & \~filters.COMMAND, h.receive_promo)
            ],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # ==================== ADMIN CONVERSATION HANDLERS ====================

    # Add Offer Conversation
    add_offer_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_offer_start, pattern="^add_offer$")],
        states={
            AdminStates.ADD_OFFER_NAME: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_name)],
            AdminStates.ADD_OFFER_DIAMONDS: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_diamonds)],
            AdminStates.ADD_OFFER_PRICE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_price)],
            AdminStates.ADD_OFFER_BUTTON: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_button)],
            AdminStates.ADD_OFFER_DESCRIPTION: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_description)],
            AdminStates.ADD_OFFER_DELIVERY: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_delivery)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Ban User Conversation
    ban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.ban_user_start, pattern="^ban_user$")],
        states={
            AdminStates.BAN_USER_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.ban_user_id)],
            AdminStates.BAN_REASON: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.ban_reason)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Unban User Conversation
    unban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.unban_user_start, pattern="^unban_user$")],
        states={
            AdminStates.UNBAN_USER_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.unban_user_id)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Add Balance Conversation
    add_balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_balance_start, pattern="^add_balance$")],
        states={
            AdminStates.ADD_BALANCE_USER: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_balance_user)],
            AdminStates.ADD_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_balance_amount)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Remove Balance Conversation
    remove_balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.remove_balance_start, pattern="^remove_balance$")],
        states={
            AdminStates.REMOVE_BALANCE_USER: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.remove_balance_user)],
            AdminStates.REMOVE_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.remove_balance_amount)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Broadcast Conversation
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.broadcast_start, pattern="^admin_broadcast$")],
        states={
            AdminStates.BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Add Promo Conversation
    add_promo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_promo_start, pattern="^admin_promo$")],
        states={
            AdminStates.ADD_PROMO_CODE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_code)],
            AdminStates.ADD_PROMO_DISCOUNT: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_discount)],
            AdminStates.ADD_PROMO_USES: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_uses)],
            AdminStates.ADD_PROMO_MIN: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_min)],
            AdminStates.ADD_PROMO_EXPIRY: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_expiry)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Search User Conversation
    search_user_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.search_user_start, pattern="^search_user$")],
        states={
            AdminStates.SEARCH_USER: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.search_user)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Search Order Conversation
    search_order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.search_order_start, pattern="^search_order$")],
        states={
            AdminStates.SEARCH_ORDER: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.search_order)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Edit Offer Value Conversation
    edit_offer_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.edit_field_selected, pattern="^edit_field_")],
        states={
            AdminStates.EDIT_OFFER_VALUE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.edit_offer_value)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Edit Setting Conversation
    edit_setting_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.edit_setting_start, pattern="^set_")],
        states={
            AdminStates.EDIT_SETTING_VALUE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.edit_setting_value)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Add Admin Conversation
    add_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_admin_start, pattern="^add_admin$")],
        states={
            AdminStates.ADD_ADMIN_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_admin_id)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # Remove Admin Conversation
    remove_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.remove_admin_start, pattern="^remove_admin$")],
        states={
            AdminStates.REMOVE_ADMIN_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.remove_admin_id)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # ==================== রেজিস্টার সব হ্যান্ডলার ====================

    # কমান্ড
    application.add_handler(CommandHandler("start", h.start))
    application.add_handler(CommandHandler("dashboard", h.dashboard))
    application.add_handler(CommandHandler("cancel", h.cancel))

    # Conversation Handlers
    application.add_handler(deposit_conv)
    application.add_handler(order_conv)
    application.add_handler(promo_conv)
    application.add_handler(add_offer_conv)
    application.add_handler(ban_conv)
    application.add_handler(unban_conv)
    application.add_handler(add_balance_conv)
    application.add_handler(remove_balance_conv)
    application.add_handler(broadcast_conv)
    application.add_handler(add_promo_conv)
    application.add_handler(search_user_conv)
    application.add_handler(search_order_conv)
    application.add_handler(edit_offer_conv)
    application.add_handler(edit_setting_conv)
    application.add_handler(add_admin_conv)
    application.add_handler(remove_admin_conv)

    # ==================== CALLBACK QUERY HANDLERS ====================

    # User Callbacks
    application.add_handler(CallbackQueryHandler(h.back_to_main, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(h.diamond_topup, pattern="^diamond_topup$"))
    application.add_handler(CallbackQueryHandler(h.special_offers, pattern="^special_offers$"))
    application.add_handler(CallbackQueryHandler(h.deposit_start, pattern="^deposit$"))
    application.add_handler(CallbackQueryHandler(h.my_account, pattern="^my_account$"))
    application.add_handler(CallbackQueryHandler(h.my_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(h.referral, pattern="^referral$"))
    application.add_handler(CallbackQueryHandler(h.support, pattern="^support$"))
    application.add_handler(CallbackQueryHandler(h.help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(h.confirm_order, pattern="^confirm_order_"))
    application.add_handler(CallbackQueryHandler(h.cancel_order, pattern="^cancel_order$"))

    # Admin Dashboard
    application.add_handler(CallbackQueryHandler(h.dashboard, pattern="^admin_dashboard$"))
    application.add_handler(CallbackQueryHandler(h.close_dashboard, pattern="^close_dashboard$"))
    application.add_handler(CallbackQueryHandler(h.admin_offers_menu, pattern="^admin_offers$"))
    application.add_handler(CallbackQueryHandler(h.admin_users_menu, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(h.admin_deposits_menu, pattern="^admin_deposits$"))
    application.add_handler(CallbackQueryHandler(h.admin_orders_menu, pattern="^admin_orders$"))
    application.add_handler(CallbackQueryHandler(h.admin_stats, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(h.admin_settings, pattern="^admin_settings$"))
    application.add_handler(CallbackQueryHandler(h.admin_management, pattern="^admin_management$"))

    # Offers
    application.add_handler(CallbackQueryHandler(h.all_offers_admin, pattern="^all_offers$"))
    application.add_handler(CallbackQueryHandler(h.delete_offer_start, pattern="^delete_offer$"))
    application.add_handler(CallbackQueryHandler(h.delete_offer_confirm, pattern="^delete_offer_"))
    application.add_handler(CallbackQueryHandler(h.edit_offer_start, pattern="^edit_offer$"))
    application.add_handler(CallbackQueryHandler(h.edit_offer_select, pattern="^edit_select_"))
    application.add_handler(CallbackQueryHandler(h.save_offer, pattern="^save_offer$"))
    application.add_handler(CallbackQueryHandler(h.cancel_add_offer, pattern="^cancel_add_offer$"))

    # Deposits
    application.add_handler(CallbackQueryHandler(h.pending_deposits, pattern="^pending_deposits$"))
    application.add_handler(CallbackQueryHandler(h.approved_deposits, pattern="^approved_deposits$"))
    application.add_handler(CallbackQueryHandler(h.rejected_deposits, pattern="^rejected_deposits$"))
    application.add_handler(CallbackQueryHandler(h.approve_deposit, pattern="^approve_deposit_"))
    application.add_handler(CallbackQueryHandler(h.reject_deposit, pattern="^reject_deposit_"))

    # Orders
    application.add_handler(CallbackQueryHandler(h.pending_orders, pattern="^pending_orders$"))
    application.add_handler(CallbackQueryHandler(h.completed_orders, pattern="^completed_orders$"))
    application.add_handler(CallbackQueryHandler(h.cancelled_orders, pattern="^cancelled_orders$"))
    application.add_handler(CallbackQueryHandler(h.process_order, pattern="^process_order_"))
    application.add_handler(CallbackQueryHandler(h.complete_order, pattern="^complete_order_"))
    application.add_handler(CallbackQueryHandler(h.cancel_order_admin, pattern="^cancel_order_admin_"))

    # Users
    application.add_handler(CallbackQueryHandler(h.all_users, pattern="^all_users$"))
    application.add_handler(CallbackQueryHandler(h.quick_ban, pattern="^quick_ban_"))
    application.add_handler(CallbackQueryHandler(h.quick_unban, pattern="^quick_unban_"))

    # Broadcast
    application.add_handler(CallbackQueryHandler(h.broadcast_all, pattern="^broadcast_all$"))
    application.add_handler(CallbackQueryHandler(h.cancel_broadcast, pattern="^cancel_broadcast$"))

    # Settings
    application.add_handler(CallbackQueryHandler(h.toggle_maintenance, pattern="^toggle_maintenance$"))

    # বট চালু
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
