#!/usr/bin/python3

# SPDX-License-Identifier: GPL-3.0-or-later

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
import store.notify as notify


for user in models.UserData.objects.all().order_by('pk'):
    notification = None
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

        charges   = models.Charge.objects \
                .filter(user=user,
                        time_stamp__gte=last_mail,
                        time_stamp__lt=user.last_mail,
                        annulled=False) \
                .annotate(count=Count('comment'), sum=Sum('amount'))

        outgoing = models.Transfer.objects \
                .filter(sender=user,
                        time_stamp__gte=last_mail,
                        time_stamp__lt=user.last_mail,
                        annulled=False) \
                .annotate(count=Count('receiver'), sum=Sum('amount'))

        incoming = models.Transfer.objects \
                .filter(receiver=user,
                        time_stamp__gte=last_mail,
                        time_stamp__lt=user.last_mail,
                        annulled=False) \
                .annotate(count=Count('sender'), sum=Sum('amount'))

        notification = notify.Bill(user, "Monatsabrechnung", purchases, charges, outgoing, incoming)
    try:
        notification.execute()
    except:
        pass
