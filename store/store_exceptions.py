class UserNotEnoughMoney(Exception):
    def __init__(self):
        super().__init__("Guthaben reicht nicht aus!")


class NotAnnullable(Exception):
    def __init__(self):
        super().__init__("Nicht annullierbar!")


class PurchaseNotAnnullable(Exception):
    def __init__(self):
        super().__init__("Einkauf ist nicht annullierbar!")
