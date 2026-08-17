from enum import Enum, auto

class UserStates(Enum):
    # Deposit
    WAITING_DEPOSIT_AMOUNT = auto()
    WAITING_TRX_ID = auto()

    # Order
    WAITING_UID = auto()

    # Promo
    WAITING_PROMO_CODE = auto()


class AdminStates(Enum):
    # Offer Add
    ADD_OFFER_NAME = auto()
    ADD_OFFER_DIAMONDS = auto()
    ADD_OFFER_PRICE = auto()
    ADD_OFFER_BUTTON = auto()
    ADD_OFFER_DESCRIPTION = auto()
    ADD_OFFER_DELIVERY = auto()

    # Offer Edit
    EDIT_OFFER_SELECT = auto()
    EDIT_OFFER_FIELD = auto()
    EDIT_OFFER_VALUE = auto()

    # User Management
    SEARCH_USER = auto()
    ADD_BALANCE_USER = auto()
    ADD_BALANCE_AMOUNT = auto()
    REMOVE_BALANCE_USER = auto()
    REMOVE_BALANCE_AMOUNT = auto()
    BAN_USER_ID = auto()
    BAN_REASON = auto()
    UNBAN_USER_ID = auto()

    # Broadcast
    BROADCAST_MESSAGE = auto()
    BROADCAST_CONFIRM = auto()

    # Promo
    ADD_PROMO_CODE = auto()
    ADD_PROMO_DISCOUNT = auto()
    ADD_PROMO_USES = auto()
    ADD_PROMO_MIN = auto()
    ADD_PROMO_EXPIRY = auto()

    # Settings
    EDIT_SETTING_VALUE = auto()

    # Admin Management
    ADD_ADMIN_ID = auto()
    REMOVE_ADMIN_ID = auto()

    # Order Search
    SEARCH_ORDER = auto()
