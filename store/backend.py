# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import timedelta
from typing import List, Dict, Tuple
from decimal import Decimal

import django.contrib.auth
import django.contrib.auth.models
from django.db import transaction
from django.db.models import F, Count
from django.http import HttpRequest
from django.utils import timezone

from typeguard import typechecked

import store.config as config
import store.exceptions as exceptions
import store.models as models
import store.notify as notify

class UserLogic:
    @staticmethod
    @typechecked
    def getUser(ident: str, ident_type: int) -> models.UserData:
        """
        Return user as given by identifier and its type.
        """

        if ident_type == models.UserIdentifier.PRIMARYKEY:
            return models.UserData.objects.get(id=ident)

        x = models.UserIdentifier.objects.filter(ident=ident, ident_type=ident_type) \
                .select_related('user') \
                .first()
        if x is None:
            # Remeber failed RFID/Barcode logins
            if ident_type == models.UserIdentifier.RFID or \
               ident_type == models.UserIdentifier.BARCODE:
                i = models.UnknownUserIdentifier(ident=ident, ident_type=ident_type)
                i.save()

            # Expire old entries
            time_stamp = timezone.now() - timedelta(days=1)
            models.UnknownUserIdentifier.objects \
                    .filter(time_stamp__lt=time_stamp) \
                    .delete()

            raise exceptions.UserIdentifierNotExists()
        return x.user

    @staticmethod
    @typechecked
    def login(request: HttpRequest, ident: str, ident_type: int) -> None:
        """
        Login user via Django's session management.
        """

        user = UserLogic.getUser(ident, ident_type)

        if ident_type == models.UserIdentifier.PRIMARYKEY and not user.shown_on_login_screen:
            raise exceptions.DisabledIdentifier()

        django.contrib.auth.login(request, user.auth)

    @staticmethod
    @typechecked
    def getFrequentUsersList() -> List[dict]:
        """
        Return list of users sorted after last login.
        """

        User = django.contrib.auth.models.User

        x = User.objects.filter(userdata__shown_on_login_screen=True) \
                .values('username', 'userdata__id') \
                .order_by(F('last_login').desc(nulls_last=True))
        return list(x)


class ProductLogic:
    @staticmethod
    @typechecked
    def getProduct(ident: str, ident_type: int) -> models.Product:
        """
        Return product as given by identifier and its type.
        """

        if ident_type == models.ProductIdentifier.PRIMARYKEY:
            try:
                return models.Product.objects.get(id=ident)
            except models.Product.DoesNotExist:
                raise exceptions.ProductIdentifierNotExists()

        x = models.ProductIdentifier.objects.filter(ident_type=ident_type).filter(ident=ident) \
                .select_related('product') \
                .first()
        if x is None:
            raise exceptions.ProductIdentifierNotExists()
        return x.product

    @staticmethod
    @typechecked
    def getMostBoughtProductsList(user_id: int) -> List[dict]:
        """
        Return list of products most often bought (time and count
        as configured).
        """

        max_products = config.N_MOST_BOUGHT_PRODUCTS
        max_days = config.T_MOST_BOUGHT_PRODUCTS_D

        time_stamp = timezone.now() - timedelta(days=max_days)
        products = models.Purchase.objects \
                .filter(user=user_id,
                        time_stamp__gte=time_stamp,
                        product__isnull=False,
                        annulled=False) \
                .select_related('product') \
                .values('product__name', 'product_id', 'product__price') \
                .annotate(total=Count('product_id')) \
                .order_by('-total')[:max_products]
        return list(products)

    @staticmethod
    @typechecked
    def getLastBoughtProductsList(user_id: int) -> List[dict]:
        """
        Return list of products last bought by this user.
        """

        max_products = config.N_LAST_BOUGHT_PRODUCTS
        annullable_time = config.T_ANNULLABLE_PURCHASE_M

        products = models.Purchase.objects \
                .filter(user=user_id, product__isnull=False) \
                .select_related('product') \
                .order_by('-time_stamp')[:max_products] \
                .values('product__name', 'product_id', 'product__price', 'time_stamp', 'id', 'annulled')

        time_limit = timezone.now() - timedelta(minutes=annullable_time)
        for product in products:
            product['purchase__id'] = product.pop('id')
            product['annullable'] = time_limit <= product['time_stamp']

        return list(products)

    @staticmethod
    @typechecked
    def getProductByCategory(category: int) -> Dict[str, List[dict]]:
        """
        Return all products as dict in the given category.
        """

        # Get sublevels
        sublevels = models.ProductCategory.objects.filter(toplevel=category).values('sublevel')

        # Get product
        products = {}
        for sublevel in sublevels:
            # Get product for sublevel
            sublevel = sublevel['sublevel']
            ps = models.ProductCategory.objects.filter(toplevel=category, sublevel=sublevel) \
                    .prefetch_related('products') \
                    .values('products__id', 'products__name', 'products__price') \
                    .all()

            # Rename keys
            for p in ps:
                p['id'] = p.pop('products__id')
                p['name'] = p.pop('products__name')
                p['price'] = p.pop('products__price')

            products[sublevel] = list(ps)

        return products

    @staticmethod
    @typechecked
    def getCandies() -> Dict[str, List[dict]]:
        return ProductLogic.getProductByCategory(models.ProductCategory.SNACK)

    @staticmethod
    @typechecked
    def getDrinks() -> Dict[str, List[dict]]:
        return ProductLogic.getProductByCategory(models.ProductCategory.GETRAENK)


class PurchaseLogic:
    @staticmethod
    @typechecked
    def purchase(user_id: int, product_ident: str, product_ident_type: int) \
            -> Tuple[int, int]:
        """
        Purchase the product for the given user and return id's of purchase
        and product.
        """

        notification = None
        with transaction.atomic():
            product = ProductLogic.getProduct(product_ident, product_ident_type)
            product.stock -= 1
            product.save()

            user = models.UserData.objects.get(id=user_id)
            user.money -= product.price
            if user.money < config.MONEY_MIN_LIMIT:
                raise exceptions.UserNotEnoughMoney()
            user.save()

            purchase = models.Purchase(user=user, product=product, price=product.price)
            purchase.save()
            notification = notify.Purchase(purchase)
        try:
            notification.execute()
        except:
            pass

        return purchase.id, product.id

    @staticmethod
    @typechecked
    def annulPurchase(purchase_id: int) -> None:
        """
        Annul the given purchase if possible (maximum time is configured).
        """

        annullable_time = config.T_ANNULLABLE_PURCHASE_M

        notification = None
        with transaction.atomic():
            purchase = models.Purchase.objects.get(id=purchase_id)

            time_limit = timezone.now() - timedelta(minutes=annullable_time)
            if time_limit >= purchase.time_stamp:
                raise exceptions.PurchaseNotAnnullable()

            user = purchase.user
            user.money += purchase.price
            user.save()
            product = purchase.product
            product.stock += 1
            product.save()
            purchase.annulled = True
            purchase.save()
            notification = notify.Purchase(purchase)
        try:
            notification.execute()
        except:
            pass


class ChargeLogic:
    @staticmethod
    @typechecked
    def getLastChargesList(user_id: int) -> List[dict]:
        """
        Return list of recent charges of this user (count capped via
        configuration).
        """

        max_charges = config.N_LAST_CHARGES
        annullable_time = config.T_ANNULLABLE_CHARGE_M
        charges = models.Charge.objects.filter(user=user_id) \
                .values('id', 'amount', 'annulled', 'time_stamp') \
                .order_by('-time_stamp')
        if max_charges >= 0:
            charges = charges[:max_charges]

        time_limit = timezone.now() - timedelta(minutes=annullable_time)
        for charge in charges:
            charge['annullable'] = time_limit <= charge['time_stamp']

        return list(charges)

    @staticmethod
    @typechecked
    def charge(user_id: int, amount: Decimal) -> int:
        """
        Charge the given amount to the given user.
        """

        assert amount > 0

        notification = None
        with transaction.atomic():
            user = models.UserData.objects.get(id=user_id)
            user.money += amount
            user.save()
            charge = models.Charge(amount=amount, user=user)
            charge.save()
            notification = notify.Charge(charge)
        try:
            notification.execute()
        except:
            pass
        return charge.id

    @staticmethod
    @typechecked
    def annulCharge(charge_id: int) -> None:
        """
        Annul the given charge if possible (maximum time is configured).
        """

        annullable_time = config.T_ANNULLABLE_CHARGE_M

        notification = None
        with transaction.atomic():
            charge = models.Charge.objects.get(id=charge_id)

            time_limit = timezone.now() - timedelta(minutes=annullable_time)
            if time_limit > charge.time_stamp:
                raise exceptions.ChargeNotAnnullable()

            user = charge.user
            user.money -= charge.amount
            if user.money < config.MONEY_MIN_LIMIT:
                raise exceptions.UserNotEnoughMoney()
            user.save()
            charge.annulled = True
            charge.save()
            notification = notify.Charge(charge)
        try:
            notification.execute()
        except:
            pass

class TransferLogic:
    @staticmethod
    @typechecked
    def getFrequentTransferTargets(user_id: int) -> List[dict]:
        """
        Return list of frequent transfer recipients of this user. First often
        used recipients of the user (count capped via configuration) followed
        by the remaining users.
        """

        max_receivers = config.N_TRANSFERS_RECEIVERS
        recent_transfers = models.Transfer.objects.filter(sender=user_id) \
                .exclude(receiver=None) \
                .select_related('receiver')

        if max_receivers >= 0:
            recent_transfers = recent_transfers[:max_receivers]

        other_transfers = models.UserData.objects.exclude(id__in=[d.receiver.id for d in list(recent_transfers)]) \
                .exclude(id=user_id) \
                .values('id', username=F('auth__username')) \
                .order_by('username')

        recent_transfers = recent_transfers.values('receiver', receiver__username=F('receiver__auth__username')) \
                .annotate(total=Count('receiver')) \
                .order_by('receiver__username').order_by('-total')

        for transfer in recent_transfers:
            transfer['id'] = transfer.pop('receiver')
            transfer['username'] = transfer.pop('receiver__username')

        return list(recent_transfers) + list(other_transfers)

    @staticmethod
    @typechecked
    def getLastTransfers(user_id: int) -> List[dict]:
        """
        Return list of recent transfers of this user (count capped via
        configuration).
        """

        max_transfers = config.N_LAST_TRANSFERS
        annullable_time = config.T_ANNULLABLE_TRANSFERS_M

        transfers = models.Transfer.objects.filter(sender=user_id) \
                .select_related('receiver') \
                .order_by('-time_stamp')[:max_transfers] \
                .values('id', 'annulled', 'amount', 'receiver__auth__username', 'time_stamp')

        time_limit = timezone.now() - timedelta(minutes=annullable_time)
        for transfer in transfers:
            transfer['annullable'] = time_limit <= transfer['time_stamp']
            transfer['receiver_username'] = transfer.pop('receiver__auth__username')

        return list(transfers)

    @staticmethod
    @typechecked
    def transfer(user_id: int, receiver_ident: str, receiver_ident_type: int,
            amount: Decimal) -> Tuple[int, int]:
        """
        Transfer money from the given user to the given recipient.
        """

        assert amount > 0

        notification = None
        with transaction.atomic():
            sender = models.UserData.objects.get(id=user_id)
            receiver = UserLogic.getUser(ident=receiver_ident, ident_type=receiver_ident_type)
            if sender.id == receiver.id:
                raise exceptions.SenderEqualsReceiverError()

            transfer = models.Transfer(sender=sender, receiver=receiver, amount=amount)
            transfer.save()

            sender.money -= amount
            if sender.money < config.MONEY_MIN_LIMIT:
                raise exceptions.UserNotEnoughMoney()
            sender.save()
            receiver.money += amount
            receiver.save()
            notification = notify.Transfer(transfer)
        try:
            notification.execute()
        except:
            pass

        return transfer.id, receiver.id

    @staticmethod
    @typechecked
    def annulTransfer(transfer_id: int) -> None:
        """
        Annul the given transfer if possible (maximum time is configured).
        """

        annullable_time = config.T_ANNULLABLE_TRANSFERS_M

        notification = None
        with transaction.atomic():
            transfer = models.Transfer.objects.get(id=transfer_id)

            time_limit = timezone.now() - timedelta(minutes=annullable_time)
            if time_limit > transfer.time_stamp:
                raise exceptions.TransferNotAnnullable()

            receiver = transfer.receiver
            sender = transfer.sender

            transfer.annulled = True
            transfer.save()
            receiver.money -= transfer.amount
            if receiver.money < config.MONEY_MIN_LIMIT:
                raise exceptions.UserNotEnoughMoney()
            receiver.save()
            sender.money += transfer.amount
            sender.save()
            notification = notify.Transfer(transfer)
        try:
            notification.execute()
        except:
            pass
