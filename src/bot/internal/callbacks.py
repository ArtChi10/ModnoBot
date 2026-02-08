from aiogram.filters.callback_data import CallbackData

from bot.internal.enums import MenuButtons, PaidEntity, SubscriptionAction


class PaidEntityCallbackFactory(CallbackData, prefix="paid_functions"):
    entity: PaidEntity


class SubscriptionActionsCallbackFactory(CallbackData, prefix="subscription_actions"):
    action: SubscriptionAction


class NewDialogCallbackFactory(CallbackData, prefix="new_dialog"):
    choice: MenuButtons
