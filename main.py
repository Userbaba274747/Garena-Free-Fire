import logging

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

from config import BOT_TOKEN
import database as db
from states import UserStates, AdminStates
import handlers as h


# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# POST INIT
# ============================================================

async def post_init(application: Application):
    """বট স্টার্ট হওয়ার সময় ডাটাবেস ইনিশিয়ালাইজ"""
    await db.init_db()
    logger.info("Database initialized successfully!")


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # APPLICATION
    # ========================================================

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )


    # ========================================================
    # USER CONVERSATION HANDLERS
    # ========================================================

    # --------------------------------------------------------
    # Deposit Conversation
    # --------------------------------------------------------

    deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.deposit_method,
                pattern=r"^deposit_(bkash|nagad|rocket|binance)$"
            )
        ],
        states={
            UserStates.WAITING_DEPOSIT_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.receive_deposit_amount
                )
            ],

            UserStates.WAITING_TRX_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.receive_trx_id
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Order UID Conversation
    # --------------------------------------------------------

    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.select_offer,
                pattern=r"^select_offer_"
            )
        ],
        states={
            UserStates.WAITING_UID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.receive_uid
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Promo Code Conversation
    # --------------------------------------------------------

    promo_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.promo_code_start,
                pattern=r"^promo_code$"
            )
        ],
        states={
            UserStates.WAITING_PROMO_CODE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.receive_promo
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # ========================================================
    # ADMIN CONVERSATION HANDLERS
    # ========================================================

    # --------------------------------------------------------
    # Add Offer Conversation
    # --------------------------------------------------------

    add_offer_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_offer_start,
                pattern=r"^add_offer$"
            )
        ],
        states={
            AdminStates.ADD_OFFER_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_name
                )
            ],

            AdminStates.ADD_OFFER_DIAMONDS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_diamonds
                )
            ],

            AdminStates.ADD_OFFER_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_price
                )
            ],

            AdminStates.ADD_OFFER_BUTTON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_button
                )
            ],

            AdminStates.ADD_OFFER_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_description
                )
            ],

            AdminStates.ADD_OFFER_DELIVERY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_delivery
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Ban User Conversation
    # --------------------------------------------------------

    ban_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.ban_user_start,
                pattern=r"^ban_user$"
            )
        ],
        states={
            AdminStates.BAN_USER_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.ban_user_id
                )
            ],

            AdminStates.BAN_REASON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.ban_reason
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Unban User Conversation
    # --------------------------------------------------------

    unban_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.unban_user_start,
                pattern=r"^unban_user$"
            )
        ],
        states={
            AdminStates.UNBAN_USER_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.unban_user_id
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Add Balance Conversation
    # --------------------------------------------------------

    add_balance_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_balance_start,
                pattern=r"^add_balance$"
            )
        ],
        states={
            AdminStates.ADD_BALANCE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_balance_user
                )
            ],

            AdminStates.ADD_BALANCE_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_balance_amount
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Remove Balance Conversation
    # --------------------------------------------------------

    remove_balance_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.remove_balance_start,
                pattern=r"^remove_balance$"
            )
        ],
        states={
            AdminStates.REMOVE_BALANCE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.remove_balance_user
                )
            ],

            AdminStates.REMOVE_BALANCE_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.remove_balance_amount
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Broadcast Conversation
    # --------------------------------------------------------

    broadcast_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.broadcast_start,
                pattern=r"^admin_broadcast$"
            )
        ],
        states={
            AdminStates.BROADCAST_MESSAGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.broadcast_message
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Add Promo Conversation
    # --------------------------------------------------------

    add_promo_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_promo_start,
                pattern=r"^admin_promo$"
            )
        ],
        states={
            AdminStates.ADD_PROMO_CODE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_code
                )
            ],

            AdminStates.ADD_PROMO_DISCOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_discount
                )
            ],

            AdminStates.ADD_PROMO_USES: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_uses
                )
            ],

            AdminStates.ADD_PROMO_MIN: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_min
                )
            ],

            AdminStates.ADD_PROMO_EXPIRY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_expiry
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Search User Conversation
    # --------------------------------------------------------

    search_user_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.search_user_start,
                pattern=r"^search_user$"
            )
        ],
        states={
            AdminStates.SEARCH_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.search_user
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Search Order Conversation
    # --------------------------------------------------------

    search_order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.search_order_start,
                pattern=r"^search_order$"
            )
        ],
        states={
            AdminStates.SEARCH_ORDER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.search_order
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Edit Offer Value Conversation
    # --------------------------------------------------------

    edit_offer_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.edit_field_selected,
                pattern=r"^edit_field_"
            )
        ],
        states={
            AdminStates.EDIT_OFFER_VALUE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.edit_offer_value
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Edit Setting Conversation
    # --------------------------------------------------------

    edit_setting_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.edit_setting_start,
                pattern=r"^set_"
            )
        ],
        states={
            AdminStates.EDIT_SETTING_VALUE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.edit_setting_value
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Add Admin Conversation
    # --------------------------------------------------------

    add_admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_admin_start,
                pattern=r"^add_admin$"
            )
        ],
        states={
            AdminStates.ADD_ADMIN_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_admin_id
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # --------------------------------------------------------
    # Remove Admin Conversation
    # --------------------------------------------------------

    remove_admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.remove_admin_start,
                pattern=r"^remove_admin$"
            )
        ],
        states={
            AdminStates.REMOVE_ADMIN_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.remove_admin_id
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True
    )


    # ========================================================
    # REGISTER COMMAND HANDLERS
    # ========================================================

    application.add_handler(
        CommandHandler("start", h.start)
    )

    application.add_handler(
        CommandHandler("dashboard", h.dashboard)
    )

    application.add_handler(
        CommandHandler("cancel", h.cancel)
    )


    # ========================================================
    # REGISTER CONVERSATION HANDLERS
    # ========================================================

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


    # ========================================================
    # USER CALLBACK QUERY HANDLERS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.back_to_main,
            pattern=r"^back_to_main$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.diamond_topup,
            pattern=r"^diamond_topup$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.special_offers,
            pattern=r"^special_offers$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.deposit_start,
            pattern=r"^deposit$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.my_account,
            pattern=r"^my_account$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.my_orders,
            pattern=r"^my_orders$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.referral,
            pattern=r"^referral$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.support,
            pattern=r"^support$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.help_command,
            pattern=r"^help$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.confirm_order,
            pattern=r"^confirm_order_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_order,
            pattern=r"^cancel_order$"
        )
    )


    # ========================================================
    # ADMIN DASHBOARD CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.dashboard,
            pattern=r"^admin_dashboard$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.close_dashboard,
            pattern=r"^close_dashboard$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_offers_menu,
            pattern=r"^admin_offers$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_users_menu,
            pattern=r"^admin_users$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_deposits_menu,
            pattern=r"^admin_deposits$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_orders_menu,
            pattern=r"^admin_orders$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_stats,
            pattern=r"^admin_stats$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_settings,
            pattern=r"^admin_settings$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_management,
            pattern=r"^admin_management$"
        )
    )


    # ========================================================
    # OFFERS CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.all_offers_admin,
            pattern=r"^all_offers$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.delete_offer_start,
            pattern=r"^delete_offer$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.delete_offer_confirm,
            pattern=r"^delete_offer_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.edit_offer_start,
            pattern=r"^edit_offer$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.edit_offer_select,
            pattern=r"^edit_select_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.save_offer,
            pattern=r"^save_offer$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_add_offer,
            pattern=r"^cancel_add_offer$"
        )
    )


    # ========================================================
    # DEPOSIT CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.pending_deposits,
            pattern=r"^pending_deposits$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.approved_deposits,
            pattern=r"^approved_deposits$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.rejected_deposits,
            pattern=r"^rejected_deposits$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.approve_deposit,
            pattern=r"^approve_deposit_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.reject_deposit,
            pattern=r"^reject_deposit_"
        )
    )


    # ========================================================
    # ORDER CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.pending_orders,
            pattern=r"^pending_orders$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.completed_orders,
            pattern=r"^completed_orders$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancelled_orders,
            pattern=r"^cancelled_orders$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.process_order,
            pattern=r"^process_order_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.complete_order,
            pattern=r"^complete_order_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_order_admin,
            pattern=r"^cancel_order_admin_"
        )
    )


    # ========================================================
    # USER MANAGEMENT CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.all_users,
            pattern=r"^all_users$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.quick_ban,
            pattern=r"^quick_ban_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.quick_unban,
            pattern=r"^quick_unban_"
        )
    )


    # ========================================================
    # BROADCAST CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.broadcast_all,
            pattern=r"^broadcast_all$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_broadcast,
            pattern=r"^cancel_broadcast$"
        )
    )


    # ========================================================
    # SETTINGS CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.toggle_maintenance,
            pattern=r"^toggle_maintenance$"
        )
    )


    # ========================================================
    # START BOT
    # ========================================================

    logger.info("Bot is starting...")

    application.run_polling(
        allowed_updates=[
            "message",
            "callback_query"
        ]
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
