# SPDX-License-Identifier: GPL-3.0-or-later

from typeguard import typechecked
from typing import Optional, Iterable

from django.db.models.query import QuerySet

from store import models

from smtplib import SMTP
from email.message import EmailMessage

class User:
    """
    Store all the information about a User required in notify
    """
    def __init__(self, user: models.UserData):
        self.data  = user
        self.money = user.money


class Notification:
    def execute(self):
        pass


class Purchase(Notification):
    """
    Notify user about a purchase
    """
    def __init__(self, obj: models.Purchase):
        pass


class Charge(Notification):
    """
    Notify user about a charge
    """
    def __init__(self, obj: models.Charge):
        self.amount   = obj.amount
        self.user     = User(obj.user)
        self.admin    = obj.admin
        self.annulled = obj.annulled

    def execute(self):
        money = format(self.amount, '.2f') + ' €'
        subject = f'Aufladung von {money}'
        if not self.annulled:
            msg = f'Deinem Konto wurden {money} gutgeschrieben.'
        else:
            subject += ' annulliert'
            msg = f'Die Aufladung deines Kontos mit {money} wurde annulliert.'
        notify(self.user, subject, msg, self.admin)


class Transfer(Notification):
    """
    Notify about a Transfer event
    """
    def __init__(self, obj: models.Transfer):
        self.amount   = obj.amount
        self.sender   = User(obj.sender)
        self.receiver = User(obj.receiver)
        self.admin    = obj.admin
        self.annulled = obj.annulled

    def execute(self):
        money = format(self.amount, '.2f') + ' €'
        if not self.annulled:
            notify(self.receiver, f'Überweisung von {self.sender.data.auth.username}',
                   f'{self.sender.data.auth.username} hat dir {money} überwiesen.',
                   self.admin)
            notify(self.sender, f'Überweisung an {self.receiver.data.auth.username}',
                   f'Du hast {money} an {self.receiver.data.auth.username} überwiesen.',
                   self.admin)
        else:
            notify(self.receiver, f'Überweisung von {self.sender.data.auth.username} annulliert',
                   f'Die Überweisung von {self.sender.data.auth.username} über {money} wurde annulliert.',
                   self.admin)
            notify(self.sender, f'Überweisung an {self.receiver.data.auth.username} annulliert',
                   f'Die Überweisung an {self.receiver.data.auth.username} über {money} wurde annulliert.',
                   self.admin)


class Bill:
    """
    Notify user about his recent activity
    """

    class Purchase:
        def __init__(self, purchase: dict):
            self.count   = purchase['count']
            self.product = purchase['product__name']
            self.sum     = purchase['sum']

    class Charge:
        def __init__(self, charge: Charge):
            self.count   = charge.count
            self.comment = charge.comment
            self.sum     = charge.sum

    class Outgoing:
        def __init__(self, transfer: Transfer):
            self.receiver = transfer.receiver.auth.username
            self.count    = transfer.count
            self.sum      = transfer.sum

    class Incoming:
        def __init__(self, transfer: Transfer):
            self.sender   = transfer.sender.auth.username
            self.count    = transfer.count
            self.sum      = transfer.sum

    def __init__(self, user: models.UserData, subject: str, purchases: QuerySet, \
                 charges: QuerySet, outgoing: QuerySet, incoming: QuerySet):
        self.user = User(user)
        self.subject = subject
        self.purchases = [Bill.Purchase(x) for x in purchases]
        self.charges   = [Bill.Charge(x) for x in charges]
        self.outgoing  = [Bill.Outgoing(x) for x in outgoing]
        self.incoming  = [Bill.Incoming(x) for x in incoming]

    def execute(self):
        blocks = []

        if len(self.purchases):
            msg = '''    Du hattest im letzten Monat:

       Menge | Artikel                                    |   Summe
      -------+--------------------------------------------+----------
'''
            
            for x in self.purchases:
                msg += f'      {x.count:6} | {x.product:42} | {x.sum:6} €\n'
            blocks.append(msg)

        if len(self.charges):
            msg = '''    Aufladungen im letzten Monat:

       Menge | Kommentar                                  |   Summe
      -------+--------------------------------------------+----------
'''
            for x in self.charges:
                msg += f'      {x.count:6} | {x.comment:42} | {x.sum:6} €\n'
            blocks.append(msg)

        if len(self.incoming) or len(self.outgoing):
            msg = '''    Überweisungen im letzten Monat:

       Menge |                                            |   Summe
      -------+--------------------------------------------+----------
'''
            for x in self.incoming:
                msg += f'      {x.count:6} | von {x.sender:38} | {x.sum:6} €\n'
            for x in self.outgoing:
                msg += f'      {x.count:6} | an {x.receiver:39} | {x.sum:6} €\n'
            blocks.append(msg)

        # Only send mails if...
        if len(blocks):
            # ... anything happend for the user
            notify(self.user, self.subject, '\n\n'.join(blocks) + '\n')
        elif self.user.money < 0:
            # ... or the user is in debt
            notify(self.user, self.subject, "")


def notify(user: User, subject: str, message: str, admin: Optional[models.UserData] = None) -> None:
    """
    Send a notification to user
    """
    name = user.data.auth.first_name if user.data.auth.first_name else user.data.auth.username
    if len(message) and not message[-1] == '\n':
        message += '\n'
    message += f"Dein aktueller Kontotstand beträgt: {user.money} €\n"

    if user.money < 0:
        message += '''
   ***************************************************
   * Dein Kontostand ist negativ. Bitte ausgleichen! *
   ***************************************************
'''
    body = f'''Hallo {name},

{message}
Deine Kaffeekasse 2020NT
'''

    if admin:
        body += f'''
PS: Die Aktion wurde durchgeführt von {admin.auth.username}
'''

    msg = EmailMessage()
    msg.set_content(body)
    msg['To'] = user.data.auth.email
    msg['From'] = 'i4kaffee@cs.fau.de'
    msg['Subject'] = f'Kaffeekasse: {subject}'

    try:
        with SMTP('localhost') as smtp:
            smtp.send_message(msg)
    except Exception as e:
        # only log the notification failure but do not abort
        # the transaction with an exception
        print(e)
