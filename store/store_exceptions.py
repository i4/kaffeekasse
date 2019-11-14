class ClientMessageException(Exception):
    """An exception which informs the client about an error."""


class UserNotEnoughMoney(ClientMessageException):
    def __init__(self):
        super().__init__("Guthaben reicht nicht aus!")


class NegativeMoneyAmount(ClientMessageException):
    def __init__(self):
        super().__init__("Positiver Betrag erwartet!")


class NotAnnullable(ClientMessageException):
    def __init__(self):
        super().__init__("Nicht annullierbar!")


class PurchaseNotAnnullable(ClientMessageException):
    def __init__(self):
        super().__init__("Einkauf ist nicht annullierbar!")


class ChargeNotAnnullable(ClientMessageException):
    def __init__(self):
        super().__init__("Aufladung ist nicht annullierbar!")


class TransferNotAnnullable(ClientMessageException):
    def __init__(self):
        super().__init__("Überweisung ist nicht annullierbar!")


class UserIdentifierNotExists(ClientMessageException):
    def __init__(self):
        super().__init__("Kein Nutzer unter der Identifikationsnummer registriert!")


class DisabledIdentifier(ClientMessageException):
    def __init__(self):
        super().__init__("Gewünschte Art der Identifizierung vom Nutzer gesperrt!")


class ProductIdentifierNotExists(ClientMessageException):
    def __init__(self):
        super().__init__("Kein Produkt unter der Identifikationsnummer registriert!")


class SenderEqualsReceiverError(ClientMessageException):
    def __init__(self):
        super().__init__("Absender darf nicht auch der Adressat sein!")
