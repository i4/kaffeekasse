#!/usr/bin/python3

# Send mails to all active users with purchases since the last run.


import os
import sys

import smtplib
from email.message import EmailMessage

sys.path.append('../')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaffeekasse.settings')
import django
django.setup()

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

import store.models as models


for user in models.UserData.objects.all().order_by('pk'):
    with transaction.atomic():
        # Fetch current version inside transaction
        user = models.UserData.objects.get(id=user.id)

        last_mail = user.last_mail
        user.last_mail = timezone.now()
        user.save()

        purchases = models.Purchase.objects \
                .filter(user=user,
                        time_stamp__gte=last_mail,
                        time_stamp__lt=user.last_mail,
                        annulled=False) \
                .values('product__name') \
                .annotate(count=Count('product__name'), sum=Sum('price'))

        # Don't send mails if the user didn't purchase anything; except for
        # users with negative money
        if len(purchases) == 0 and user.money >= 0:
            continue

        body = '''\
Hallo {},

Aktueller Kontostand: {} €
'''.format(user.auth.username, user.money)
        if user.money < 0:
            body += '''
       ***************************************************
       * Dein Kontostand ist negativ. Bitte ausgleichen! *
       ***************************************************
'''

        if len(purchases) > 0:
            body += '''
Du hattest im letzten Monat:

   Menge | Artikel                                      |  Summe
  -------+----------------------------------------------+--------
'''
            for x in purchases:
                body += '   {:5} | {:44} | {:6}\n'.format(
                        x['count'], x['product__name'], x['sum'])
        body += '''
Deine Kaffekasse 2020NT
'''

        msg = EmailMessage()
        msg.set_content(body)
        msg['To'] = user.auth.email
        msg['From'] = 'i4kaffee@cs.fau.de'
        msg['Subject'] = 'Kaffeekasse: Monatsabrechnung'

        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()
