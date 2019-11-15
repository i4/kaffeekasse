from datetime import date, timedelta, datetime
from typing import List, Dict, Tuple
from decimal import Decimal

from django.contrib.auth import login
from django.db import transaction
from django.db.models import Count
from django.http import HttpRequest

import pytz
from typeguard import typechecked

import store.models as models
import store.store_exceptions as exceptions
from store.store_config import KAFFEEKASSE as config


class UserLogic:
    @staticmethod
    @typechecked
    def getUser(ident: str, ident_type: int) -> models.User:
        """
        Return user as given by identifier and its type.
        """

        if ident_type == models.UserIdentifier.PRIMARYKEY:
            return models.User.objects.get(id=ident)

        x = models.UserIdentifier.objects.filter(ident=ident, ident_type=ident_type) \
                .select_related('user') \
                .first()
        if x is None:
            raise exceptions.UserIdentifierNotExists()
        return x.user

    @staticmethod
    @typechecked
    def login(request: HttpRequest, ident: str, ident_type: int) -> None:
        """
        Login user via Django's session management and store login date in
        database.
        """

        user = UserLogic.getUser(ident, ident_type)

        if ident_type == models.UserIdentifier.PRIMARYKEY and not user.pk_login_enabled:
            raise exceptions.DisabledIdentifier()

        with transaction.atomic():
            x = models.Login(user=user)
            x.save()
            login(request, user)

    @staticmethod
    @typechecked
    def getFrequentUsersList() -> List[dict]:
        """
        Return list of users with frequent logins. First recent logins (count
        capped via configuration), then, users with at least one login,
        followed by the remaining users.
        """

        max_users = config['N_USERS_LOGIN']
        max_days = config['T_USERS_LOGIN_D']
        time_stamp = date.today() - timedelta(days=max_days)

        recent_logins = models.Login.objects.filter(time_stamp__gte=time_stamp) \
                .select_related('user') \
                .filter(user__pk_login_enabled=True) \
                .values('user__username', 'user__id') \
                .annotate(total=Count('user__id')) \
                .order_by('-total')
        if max_users > 0:
            recent_logins = recent_logins[:max_users]

        old_logins = models.Login.objects.all() \
                .select_related('user') \
                .filter(user__pk_login_enabled=True) \
                .values('user__username', 'user__id') \
                .exclude(user__id__in=[d['user__id'] for d in list(recent_logins)]) \
                .annotate(total=Count('user__id')) \
                .order_by('-total')

        no_logins = models.User.objects.filter(pk_login_enabled=True) \
                .exclude(id__in=[d['user__id'] for d in list(recent_logins) + list(old_logins)]) \
                .order_by('username') \
                .values('username', 'id') \
                .annotate(total=Count('id'))

        for login in no_logins:
            login['user__id'] = login.pop('id')
            login['user__username'] = login.pop('username')
            login['total'] = 0

        return list(recent_logins) + list(old_logins) + list(no_logins)


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
    def getMostBoughtProductsList() -> List[dict]:
        """
        Return list of products most often bought (time and count
        as configured).
        """

        max_products = config['N_MOST_BOUGHT_PRODUCTS']
        max_days = config['T_MOST_BOUGHT_PRODUCTS_D']

        time_stamp = date.today() - timedelta(days=max_days)
        products = models.Purchase.objects \
                .filter(time_stamp__gte=time_stamp, product__isnull=False) \
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

        max_products = config['N_LAST_BOUGHT_PRODUCTS']
        annullable_time = config['T_ANNULLABLE_PURCHASE_M']

        products = models.Purchase.objects \
                .filter(user=user_id, product__isnull=False) \
                .select_related('product') \
                .order_by('-time_stamp')[:max_products] \
                .values('product__name', 'product_id', 'product__price', 'time_stamp', 'id', 'annulled')

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        for product in products:
            product['purchase__id'] = product.pop('id')
            purchase_time = product['time_stamp']
            if time_limit >= purchase_time or product['annulled']:
                product.update({'annullable': False})
            else:
                product.update({'annullable': True})

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
            sublevel = sublevel["sublevel"]
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

        with transaction.atomic():
            product = ProductLogic.getProduct(product_ident, product_ident_type)
            product.stock -= 1
            product.save()

            user = models.User.objects.get(id=user_id)
            user.money -= product.price
            if user.money < 0:
                raise exceptions.UserNotEnoughMoney()
            user.save()

            purchase = models.Purchase(user=user, product=product, price=product.price, annulled=False)
            purchase.save()

            return purchase.id, product.id

    @staticmethod
    @typechecked
    def annulPurchase(purchase_id: int) -> None:
        """
        Annul the given purchase if possible (maximum time is configured).
        """

        annullable_time = config['T_ANNULLABLE_PURCHASE_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        purchase = models.Purchase.objects.get(id=purchase_id)

        purchase_time = purchase.time_stamp
        if time_limit >= purchase_time:
            raise exceptions.PurchaseNotAnnullable()

        with transaction.atomic():
            user = models.User.objects.get(id=purchase.user.id)
            user.money += purchase.price
            user.save()
            purchase.annulled = True
            purchase.save()


class ChargeLogic:
    @staticmethod
    @typechecked
    def getLastChargesList(user_id: int) -> List[dict]:
        """
        Return list of recent charges of this user (count capped via
        configuration).
        """

        max_charges = config['N_LAST_CHARGES']
        annullable_time = config['T_ANNULLABLE_CHARGE_M']
        charges = models.Charge.objects.filter(user=user_id) \
                .values('id', 'amount', 'annulled', 'time_stamp') \
                .order_by('-time_stamp')
        if max_charges >= 0:
            charges = charges[:max_charges]

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        for charge in charges:
            if time_limit > charge['time_stamp']:
                charge.update({'annullable': False})
            else:
                charge.update({'annullable': True})

        return list(charges)

    @staticmethod
    @typechecked
    def charge(user_id: int, amount: Decimal) -> int:
        """
        Charge the given amount to the given user.
        """

        assert amount > 0

        with transaction.atomic():
            user = models.User.objects.get(id=user_id)
            user.money += amount
            user.save()
            charge = models.Charge(amount=amount, annulled=False, user_id=user.id)
            charge.save()
            return charge.id

    @staticmethod
    @typechecked
    def annulCharge(charge_id: int) -> None:
        """
        Annul the given charge if possible (maximum time is configured).
        """

        annullable_time = config['T_ANNULLABLE_CHARGE_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        charge = models.Charge.objects.get(id=charge_id)

        if time_limit > charge.time_stamp:
            raise exceptions.ChargeNotAnnullable()

        with transaction.atomic():
            user = models.User.objects.get(id=charge.user.id)
            user.money -= charge.amount
            if user.money < 0:
                raise exceptions.UserNotEnoughMoney()
            user.save()
            charge.annulled = True
            charge.save()


class TransferLogic:
    @staticmethod
    @typechecked
    def getFrequentTransferTargets(user_id: int) -> List[dict]:
        """
        Return list of frequent transfer recipients of this user. First often
        used recipients of the user (count capped via configuration) followed
        by the remaining users.
        """

        max_receivers = config['N_TRANSFERS_RECEIVERS']
        recent_transfers = models.Transfer.objects.filter(sender=user_id) \
                .exclude(receiver=None) \
                .select_related('receiver')

        if max_receivers >= 0:
            recent_transfers = recent_transfers[:max_receivers]

        other_transfers = models.User.objects.exclude(id__in=[d.receiver.id for d in list(recent_transfers)]) \
                .exclude(id=user_id) \
                .values('id', 'username') \
                .order_by('username')

        recent_transfers = recent_transfers.values('receiver', 'receiver__username') \
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

        max_transfers = config['N_LAST_TRANSFERS']
        annullable_time = config['T_ANNULLABLE_TRANSFERS_M']

        transfers = models.Transfer.objects.filter(sender=user_id) \
                .select_related('receiver') \
                .order_by('-time_stamp')[:max_transfers] \
                .values('id', 'annulled', 'amount', 'receiver__username', 'time_stamp')

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        for transfer in transfers:
            if time_limit > transfer['time_stamp']:
                transfer.update({'annullable': False})
            else:
                transfer.update({'annullable': True})
            transfer['receiver_username'] = transfer.pop('receiver__username')

        return list(transfers)

    @staticmethod
    @typechecked
    def transfer(user_id: int, receiver_ident: str, receiver_ident_type: int,
            amount: Decimal) -> Tuple[int, int]:
        """
        Transfer money from the given user to the given recipient.
        """

        assert amount > 0

        sender = models.User.objects.get(id=user_id)
        receiver = UserLogic.getUser(ident=receiver_ident, ident_type=receiver_ident_type)
        if sender.id == receiver.id:
            raise exceptions.SenderEqualsReceiverError()

        with transaction.atomic():
            transfer = models.Transfer(sender=sender, receiver=receiver, amount=amount, annulled=False)
            transfer.save()

            sender.money -= amount
            if sender.money < 0:
                raise exceptions.UserNotEnoughMoney()
            sender.save()
            receiver.money += amount
            receiver.save()

            return transfer.id, receiver.id

    @staticmethod
    @typechecked
    def annulTransfer(transfer_id: int) -> None:
        """
        Annul the given transfer if possible (maximum time is configured).
        """

        annullable_time = config['T_ANNULLABLE_TRANSFERS_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        transfer = models.Transfer.objects.get(id=transfer_id)
        if time_limit > transfer.time_stamp:
            raise exceptions.TransferNotAnnullable()

        receiver = models.User.objects.get(id=transfer.receiver_id)
        sender = models.User.objects.get(id=transfer.sender_id)

        with transaction.atomic():
            transfer.annulled = True
            transfer.save()
            receiver.money -= transfer.amount
            if receiver.money < 0:
                raise exceptions.UserNotEnoughMoney()
            receiver.save()
            sender.money += transfer.amount
            sender.save()
