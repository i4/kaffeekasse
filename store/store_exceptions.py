from psycopg2.extensions import TransactionRollbackError
from django.db import OperationalError


class UserNotEnoughMoney(Exception):
    def __init__(self):
        super().__init__("Guthaben reicht nicht aus!")


class NegativeMoneyAmount(Exception):
    def __init__(sefl):
        super().__init__("Positiver Betrag erwartet!")


class NotAnnullable(Exception):
    def __init__(self):
        super().__init__("Nicht annullierbar!")


class PurchaseNotAnnullable(Exception):
    def __init__(self):
        super().__init__("Einkauf ist nicht annullierbar!")


class ChargeNotAnnullable(Exception):
    def __init__(self):
        super().__init__("Aufladung ist nicht annullierbar!")


class TransferNotAnnullable(Exception):
    def __init__(self):
        super().__init__("Überweisung ist nicht annullierbar!")


class UserIdentifierNotExists(Exception):
    def __init__(self):
        super().__init__("Kein Nutzer unter der Identifikationsnummer registriert!")


class DisabledIdentifier(Exception):
    def __init__(self):
        super().__init__("Gewünschte Art der Identifizierung vom Nutzer gesperrt!")


class ProductIdentifierNotExists(Exception):
    def __init__(self):
        super().__init__("Kein Produkt unter der Identifikationsnummer registriert!")


class SerializationError(Exception):
    def __init__(self):
        super().__init__("Etwas ist schief gelaufen. Bitte versuch es erneut!")
        

def filterOperationalError(exception):
    if exception.__cause__.__class__ == TransactionRollbackError:
        raise SerializationError()
    else:
        raise exception

class SenderEqualsReceiverError(Exception):
    def __init__(self):
        super().__init__("Absender darf nicht auch der Adressat sein!")

