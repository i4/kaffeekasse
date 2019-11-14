from typeguard import typechecked
from typing import List, Dict, Tuple

from .models import *
from .store_exceptions import *
from django.contrib.auth import login
from django.db.models import Count, ObjectDoesNotExist
from django.db.models.functions import Lower
from datetime import date, timedelta, datetime
from django.db import transaction
from .store_config import KAFFEEKASSE as config
from django.http import HttpRequest
import pytz


class UserLogic:
    @staticmethod
    @typechecked
    def getUser(ident: str, ident_type: int) -> User:
        """
        Returns user that can be definitely identified by the unique
        combination ident and ident_type.
        """

        if ident_type == UserIdentifier.PRIMARYKEY:
            return User.objects.get(id=ident)

        x = UserIdentifier.objects.filter(ident=ident, ident_type=ident_type) \
                .select_related('user') \
                .first()
        if x is None:
            raise UserIdentifierNotExists()
        return x.user

    @staticmethod
    @typechecked
    def login(request: HttpRequest, ident: str, ident_type: int) -> None:
        """
        Basic login function. On success the user is logged in and True is
        returned and a login-tuple is created. On Failure nothing happens and
        False is returned.
        """

        user = UserLogic.getUser(ident, ident_type)

        if ident_type == UserIdentifier.PRIMARYKEY and not user.pk_login_enabled:
            raise DisabledIdentifier()

        with transaction.atomic():
            x = Login(user=user)
            x.save()
            login(request, user)

    @staticmethod
    @typechecked
    def getFrequentUsersList() -> List[dict]:
        """
        Concatenates the results of three db-queries:

        - First part of the list: a number of users specified in max_users,
          that have most logins within a number of days specified in max_days.
        - Second part of the list: all users that are not included in the
          first part of the list and have at least one login
        - Third part of the list: all users that are not included in the first
          both parts
        """

        max_users = config['N_USERS_LOGIN']
        max_days = config['T_USERS_LOGIN_D']
        time_stamp = date.today() - timedelta(days=max_days)

        recent_logins = Login.objects.filter(time_stamp__gte=time_stamp) \
                .select_related('user') \
                .filter(user__pk_login_enabled=True) \
                .values('user__username', 'user__id') \
                .annotate(total=Count('user__id')) \
                .order_by('-total')
        if max_users > 0:
            recent_logins = recent_logins[:max_users]

        old_logins = Login.objects.all() \
                .select_related('user') \
                .filter(user__pk_login_enabled=True) \
                .values('user__username', 'user__id') \
                .exclude(user__id__in=[d['user__id'] for d in list(recent_logins)]) \
                .annotate(total=Count('user__id')) \
                .order_by('-total')

        no_logins = User.objects.filter(pk_login_enabled=True) \
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
    def getProduct(ident: str, ident_type: int) -> Product:
        """
        Returns product that can be definitely identified by the unique
        combination ident and ident_type.
        """

        if ident_type == ProductIdentifier.PRIMARYKEY:
            try:
                return Product.objects.get(id=ident)
            except Product.DoesNotExist:
                raise ProductIdentifierNotExists()

        x = ProductIdentifier.objects.filter(ident_type=ident_type).filter(ident=ident) \
                .select_related('product') \
                .first()
        if x is None:
            raise ProductIdentifierNotExists()
        return x.product

    @staticmethod
    @typechecked
    def getMostBoughtProductsList() -> List[dict]:
        """
        Result of a db query asking for a number of products specified in
        max_products that were most bought within the last max_days number of
        days.
        """

        max_products = config['N_MOST_BOUGHT_PRODUCTS']
        max_days = config['T_MOST_BOUGHT_PRODUCTS_D']

        time_stamp = date.today() - timedelta(days=max_days)
        products = Purchase.objects \
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
        Result of a db query asking for a number of products specified in
        max_products that were recently bought by a specified user. The result
        also contains information on the state of a possible annulation of the
        products purchase.
        """

        max_products = config['N_LAST_BOUGHT_PRODUCTS']
        annullable_time = config['T_ANNULLABLE_PURCHASE_M']

        products = Purchase.objects.filter(user=user_id) \
                .select_related('product') \
                .order_by('-time_stamp')[:max_products] \
                .values('product__name', 'product_id', 'product__price', 'time_stamp', 'id', 'annullated')

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        for product in products:
            product['purchase__id'] = product.pop('id')
            purchase_time = product['time_stamp']
            if time_limit >= purchase_time or product['annullated']:
                product.update({'annullable': False})
            else:
                product.update({'annullable': True})

        return list(products)

    @staticmethod
    @typechecked
    def getProductByCategory(category: int) -> Dict[str, List[dict]]:
        """
        Returns a dict with a key for each sublevel category containing all
        products, where the toplevel category equals to the input category
        """

        # Get sublevels
        sublevels = ProductCategory.objects.filter(toplevel=category).values('sublevel')

        # Get product
        products = {}
        for sublevel in sublevels:
            # Get product for sublevel
            sublevel = sublevel["sublevel"]
            ps = ProductCategory.objects.filter(toplevel=category, sublevel=sublevel) \
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
        return ProductLogic.getProductByCategory(ProductCategory.SNACK)

    @staticmethod
    @typechecked
    def getDrinks() -> Dict[str, List[dict]]:
        return ProductLogic.getProductByCategory(ProductCategory.GETRAENK)


class PurchaseLogic:
    @staticmethod
    @typechecked
    def purchase(user_id: int, product_ident: str, product_ident_type: int) \
            -> Tuple[int, int]:
        """
        Execute the purchase logic. Three db relations are included:

        *)  Purchase: include a new purchase-tuple with the user_id,
            product_id, the current time, the current products price
        *)  User: update the users money
        *)  Product: update the product stock
        """

        try:
            with transaction.atomic():
                product = ProductLogic.getProduct(product_ident, product_ident_type)
                product.stock -= 1
                product.save()

                user = User.objects.get(id=user_id)
                user.money -= product.price
                if user.money < 0:
                    raise UserNotEnoughMoney()
                user.save()

                purchase = Purchase(user=user, product=product, price=product.price, annullated=False)
                purchase.save()

                return purchase.id, product.id

        except (ObjectDoesNotExist, ProductIdentifierNotExists):
            return -1, -1
        assert False

    @staticmethod
    @typechecked
    def annullatePurchase(purchase_id: int) -> None:
        """
        Try to annullate a purchase performed by a specified user. This will
        only fail if the purchase was performed too long ago.
        """

        annullable_time = config['T_ANNULLABLE_PURCHASE_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        purchase = Purchase.objects.get(id=purchase_id)

        purchase_time = purchase.time_stamp
        if time_limit >= purchase_time:
            raise PurchaseNotAnnullable()

        with transaction.atomic():
            user = User.objects.get(id=purchase.user.id)
            user.money += purchase.price
            user.save()
            purchase.annullated = True
            purchase.save()


class ChargeLogic:
    @staticmethod
    @typechecked
    def getLastChargesList(user_id: int) -> List[dict]:
        """
        Result of a db query asking for a number of charges specified in
        max_charges that were recently performed by a specified user. The
        result also contains information on the state of a possible
        annullation of the charge.
        """

        max_charges = config['N_LAST_CHARGES']
        annullable_time = config['T_ANNULLABLE_CHARGE_M']
        charges = Charge.objects.filter(user=user_id) \
                .values('id', 'amount', 'annullated', 'time_stamp') \
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
        Executes the charge logic. Two db relations are included:
        *)  User, where the new money is add to the user money
        *)  Charge, where the new charge is saved to
        """

        assert amount > 0

        with transaction.atomic():
            user = User.objects.get(id=user_id)
            user.money += amount
            user.save()
            charge = Charge(amount=amount, annullated=False, user_id=user.id)
            charge.save()
            return charge.id

    @staticmethod
    @typechecked
    def annullateCharge(charge_id: int) -> None:
        """
        Try to annullate a charge performed by a specified user. This will
        fail if either the charge was performed too long ago or the user has
        less money on it's account than the amount of money charged.
        """

        annullable_time = config['T_ANNULLABLE_CHARGE_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        charge = Charge.objects.get(id=charge_id)

        if time_limit > charge.time_stamp:
            raise ChargeNotAnnullable()

        with transaction.atomic():
            user = User.objects.get(id=charge.user.id)
            user.money -= charge.amount
            if user.money < 0:
                raise UserNotEnoughMoney()
            user.save()
            charge.annullated = True
            charge.save()


class TransferLogic:
    @staticmethod
    @typechecked
    def getFreuquentTransferTargets(user_id: int) -> List[dict]:
        """
        Result of a db query asking for a number of receivers specified in
        max_receivers that are often addresed by a specified user Concatinates
        the result of two db queries:

        First part of the list: a number of receivers specified in
        max_receivers that are often addressed by a specific user

        Second part of the list: all users excluded the users form the first
        part and the user itself
        """

        max_receivers = config['N_TRANSFERS_RECEIVERS']
        recent_transfers = Transfer.objects.filter(sender=user_id) \
                .exclude(receiver=None) \
                .select_related('receiver')

        if max_receivers >= 0:
            recent_transfers = recent_transfers[:max_receivers]

        other_transfers = User.objects.exclude(id__in=[d.receiver.id for d in list(recent_transfers)]) \
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
        Result of a db query asking for a number of transfers that have been
        recently performed by a specified user. Also returns information on
        the state of possible annullation of the transfer.
        """

        max_transfers = config['N_LAST_TRANSFERS']
        annullable_time = config['T_ANNULLABLE_TRANSFERS_M']

        transfers = Transfer.objects.filter(sender=user_id) \
                .select_related('receiver') \
                .order_by('-time_stamp')[:max_transfers] \
                .values('id', 'annullated', 'amount', 'receiver__username', 'time_stamp')

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
        Performs the transfer routine where a sender sends money to a
        receiver. Two db relations are included:

        *)  User, where the sender aswell as the receiver are from
        *)  Transfer, where the newly created transfer is saved to
        """

        assert amount > 0

        sender = User.objects.get(id=user_id)
        receiver = UserLogic.getUser(ident=receiver_ident, ident_type=receiver_ident_type)
        if sender.id == receiver.id:
            raise SenderEqualsReceiverError()

        with transaction.atomic():
            transfer = Transfer(sender=sender, receiver=receiver, amount=amount, annullated=False)
            transfer.save()

            sender.money -= amount
            if sender.money < 0:
                raise UserNotEnoughMoney()
            sender.save()
            receiver.money += amount
            receiver.save()

            return transfer.id, receiver.id

    @staticmethod
    @typechecked
    def annullateTransfer(transfer_id: int) -> None:
        """
        Try to annullate a transfer performed by a specified user. This will
        fail if either the transfer was performed too long ago or the receiver
        of the money has less money on it's account than the amount of money
        transfered.
        """

        annullable_time = config['T_ANNULLABLE_TRANSFERS_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        transfer = Transfer.objects.get(id=transfer_id)
        if time_limit > transfer.time_stamp:
            raise TransferNotAnnullable()

        receiver = User.objects.get(id=transfer.receiver_id)
        sender = User.objects.get(id=transfer.sender_id)

        with transaction.atomic():
            transfer.annullated = True
            transfer.save()
            receiver.money -= transfer.amount
            if receiver.money < 0:
                raise UserNotEnoughMoney()
            receiver.save()
            sender.money += transfer.amount
            sender.save()
