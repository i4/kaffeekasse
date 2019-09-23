from .models import *
from .store_exceptions import *
from django.contrib.auth import login
from django.db.models import Count, ObjectDoesNotExist
from django.db.models.functions import Lower
from datetime import date, timedelta, datetime
from django.db import transaction, IntegrityError
from .store_config import KAFFEEKASSE as config
import pytz


class UserLogic:

    """
    Basic login function. On success the user is logged in and True is returned and a login-tuple is created. On Failure nothing happens and False is
    returned.
    @param request: the request object
    @param user_id: id of the user that should log in
    """
    @staticmethod
    def login(request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None
        if user is not None:
            with transaction.atomic():
                login_tuple = Login(user=user)
                login_tuple.save()
                login(request, user)
                return True
        return False

    """
    Collects the users that have the most log ins on a client within a given time period. The rest of the list is filled
    first with all other logins and than all users that have never logged in
    Returns a list of dictionaries on succes: [{'user__nickname': '...', 'user__id': ..., 'total': ...}, ...]
    @config-param max_users: the maximum of users that should be shown from the most recent ones. Depends on N_USERS_LOGIN
    @config-param max_days: the maximum of days that have passed since the last login to count as recent login. Depends on T_USERS_LOGIN_D
    """
    @staticmethod
    def getFrequentUsersList():
        max_users = config['N_USERS_LOGIN']
        max_days = config['T_USERS_LOGIN_D']
        time_stamp = date.today() - timedelta(days=max_days)

        recent_logins = Login.objects.filter(time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        recent_logins = recent_logins.select_related('user')
        recent_logins = recent_logins.values('user__nickname', 'user__id')
        recent_logins = recent_logins.annotate(total=Count('user__id'))
        if max_users <= 0:
            recent_logins = recent_logins.order_by('total').reverse()
        else:
            recent_logins = recent_logins.order_by('total').reverse()[:max_users]

        old_logins = Login.objects.all()
        old_logins = old_logins.select_related('user')
        old_logins = old_logins.values('user__nickname', 'user__id')
        old_logins = old_logins.exclude(user__id__in=[d['user__id'] for d in list(recent_logins)])
        old_logins = old_logins.annotate(total=Count('user__id'))
        old_logins = old_logins.order_by('total').reverse()
        
        no_logins = User.objects.exclude(id__in=[d['user__id'] for d in list(recent_logins) + list(old_logins)])
        no_logins = no_logins.order_by('nickname')
        no_logins = no_logins.values('nickname', 'id')
        no_logins = no_logins.annotate(total=Count('id'))

        for login in no_logins:
            login['user__id'] = login.pop('id')
            login['user__nickname'] = login.pop('nickname')
            login['total'] = 0

        return list(recent_logins) + list(old_logins) + list(no_logins)
    

class ProductLogic:

    """
    Collects the prodcuts that are most bought within a given time period.
    Returns a list of dictionries on success: [{'product__name': '...', 'product_id': ...,  'product__price': ..., 'total': ...}, ...]
    @conifg-param max_products: the maximum of products that should be shown. Depends on N_MOST_BOUGHT_PRODUCTS
    @config-param max_days: the maximum of days that have passed since the last logisince the purchase. Depends on
        T_MOST_BOUGHT_PRODUCTS_D
    """
    @staticmethod
    def getMostBoughtProductsList():
        max_products = config['N_MOST_BOUGHT_PRODUCTS']
        max_days = config['T_MOST_BOUGHT_PRODUCTS_D']
        time_stamp = date.today() - timedelta(days=max_days)
        products = Purchase.objects.filter(time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        products = products.select_related('product')
        products = products.values('product__name', 'product_id', 'product__price')
        products = products.annotate(total=Count('product_id'))
        products = products.order_by('total').reverse()[:max_products]
        return list(products)

    """
    Collects the products that are most bought by one user.
    Returns a list of dictionaries on success: [{'product__name': '...', 'product_id': 41, 'product__price': ...,
    'purchase__id': ...,  'annullated': ..., time_stamp': ..., 'annullable': ...}]
    @param user_id: the id of the user
    @config-param max_products: the maximum of products that should be shown, depends on N_LAST_BOUGHT_PRODUCTS
    @config-param annullable_time: the maximum time in minutes a purchase can be annullated. Depends on T_ANNULLABLE_PURCHASE_M
    """
    @staticmethod
    def getLastBoughtProductsList(user_id):
        max_products = config['N_LAST_BOUGHT_PRODUCTS']
        annullable_time = config['T_ANNULLABLE_PURCHASE_M']
        products = Purchase.objects.filter(user=user_id)
        products = products.select_related('product')
        products = products.order_by('time_stamp').reverse()[:max_products]
        products = products.values('product__name', 'product_id', 'product__price', 'time_stamp', 'id', 'annullated')

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        now = datetime.now()
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


class TokenLogic:

    """
    Generates a new and unique token as 64-bit integer to be used in a at-most-once client-server-interaction.
    """
    @staticmethod
    def get_token():
        with transaction.atomic():
            token = list(Token.objects.all())[0]
            token.increment()
            return token.token


class PurchaseLogic:

    """
    Execute the purchase logic. Three db parties are included:
    *)  Purchase: include a new purchase-tuple with the user_id, product_id, the current time, the current products price
        and the unique token
    *)  User: update the users money
    *)  Product: update the product stock
    @param user_id: the id of the user
    @param product_id: the id of the product
    @param token: the unique transaction-token generated by the get_token function
    """
    @staticmethod
    def purchase(user_id, product_id, token):
        try:
            with transaction.atomic():
                user = list(User.objects.filter(id=user_id))[0]
                product = list(Product.objects.filter(id=product_id))[0]
                purchase_create_return_tuple = PurchaseLogic.__createPurchaseTuple(user, product, token)
                PurchaseLogic.__updateUserMoney(user, product.price)
                PurchaseLogic.__updateProductStock(product)
        except ObjectDoesNotExist:
            return -1
        except IntegrityError:
            purchase = list(Purchase.objects.filter(token=token))[0]
            return purchase.id
        return purchase_create_return_tuple[1]

    @staticmethod
    def __createPurchaseTuple(user, product, token):
        purchase = Purchase(user=user, product=product, price=product.price, token=token, annullated=False)
        purchase.save()
        return True, purchase.id

    @staticmethod
    def __updateUserMoney(user, price):
        return user.updateMoney(price * (-1))

    @staticmethod
    def __updateProductStock(product):
        product.updateStock(-1)

    """
    Annulates a purchase that is not older than a given number of minutes. Returns False, if the purchase is too old,
    returns True else.
    @param purchase_id: the id of the purchase to annullate
    @config-param annullable_time: depends on T_ANNULLABLE_PURCHASE_M
    """
    @staticmethod
    def annullatePurchase(purchase_id, token):
        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        annullable_time = config['T_ANNULLABLE_PURCHASE_M']

        now = datetime.now()
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        purchase = list(Purchase.objects.filter(id=purchase_id))[0]
        purchase_time = purchase.time_stamp
        if time_limit >= purchase_time:
            raise PurchaseNotAnnullable()

        with transaction.atomic():
            user = list(User.objects.filter(id=purchase.user.id))[0]
            purchase.annullate()
            user.updateMoney(purchase.price)


class ChargeLogic:

    """
    Returns a list of the last charges of a specified user: [{'id': ..., 'amount': Decimal(...,...), 'annullated': ...,
    'time_stamp': ..., 'annullable': ...}]
    @param user_id: the id of the specified user
    @config-param max_charges: Number of charges to be shown. Depends on N_LAST_CHARGES
    @config-param annullable_time: time to annullate a charge. Depends on T_ANNULLABLE_CHARGE_M
    """
    @staticmethod
    def getLastChargesList(user_id):
        max_charges = config['N_LAST_CHARGES']
        annullable_time = config['T_ANNULLABLE_CHARGE_M']
        charges = Charge.objects.filter(user=user_id).values('id', 'amount', 'annullated', 'time_stamp')

        if max_charges < 0:
            charges = list(charges.order_by('time_stamp').reverse())
        else:
            charges = list(charges.order_by('time_stamp').reverse())[:max_charges]

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        now = datetime.now()
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        for charge in charges:
            if time_limit > charge['time_stamp']:
                charge.update({'annullable': False})
            else:
                charge.update({'annullable': True})

        return charges

    """
    Executes the charge logic.
    @param user_id: id of the user that charges
    @param amount: the amount of money to be charged
    @param token: the unique token got by getToken()
    """
    @staticmethod
    def charge(user_id, amount, token):
        try:
            with transaction.atomic():
                user = list(User.objects.filter(id=user_id))[0]
                charge_id = ChargeLogic.__createChargeTuple(user, amount, token)
                ChargeLogic.__updateUserMoney(user, amount)
        except IntegrityError:
            charge = list(Charge.objects.filter(token=token).values('id'))[0]
            return charge['id']
        return charge_id

    @staticmethod
    def __createChargeTuple(user, amount, token):
        charge = Charge(token=token, amount=amount, annullated=False, user_id=user.id)
        charge.save()
        return charge.id

    @staticmethod
    def __updateUserMoney(user, amount):
        user.updateMoney(amount)

    """
    Annulates a charge that is not older than a given number of minutes. Returns False, if the purchase is too old,
    returns True else.
    @param charge_id: the id of the purchase to annullate
    @config-param annullable_time: depends on T_ANNULLABLE_CHARGE_M
    """
    @staticmethod
    def annullateCharge(charge_id, token):
        annullable_time = config['T_ANNULLABLE_CHARGE_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        now = datetime.now()
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        charge = list(Charge.objects.filter(id=charge_id))[0]

        if time_limit > charge.time_stamp:
            raise ChargeNotAnnullable()

        with transaction.atomic():
            user = list(User.objects.filter(id=charge.user.id))[0]
            charge.annullate()
            user.updateMoney((-1) * charge.amount)


class TransferLogic:
    """
    Returns a list of users that are possible recepiants for a transfer of money. The list first containts receivers
    that are often addressed by the specified user and after that users that have never been addressed.
    @param user_id: the id of the user thats receivers should be shown
    @config-param max_receivers: depends on N_TRANSFERS_RECEIVERS
    """ 
    @staticmethod
    def getFreuquentTransferTargeds(user_id):
        max_receivers = config['N_TRANSFERS_RECEIVERS']
        transfers = Transfer.objects.filter(sender=user_id).exclude(receiver=None)
        transfers = transfers.select_related('receiver')
        transfers = transfers.values('receiver', 'receiver__nickname')
        transfers = transfers.annotate(total=Count('receiver'))
        transfers = transfers.order_by('receiver__nickname').order_by('total').reverse()
        if max_receivers >= 0:
            transfers = transfers[:max_receivers]

        for transfer in transfers:
            transfer['id'] = transfer.pop('receiver')
            transfer['nickname'] = transfer.pop('receiver__nickname')

        return list(transfers)

    """
    Returns a list of last transfers of a specified user sorted by the time of the transfer.
    @param user_id: the id of the user that is logged in and wants to send money
    @config-param max_transfers: depends on N_LAST_TRANSFERS
    @config-param annullable_time: depends on T_ANNULLABLE_TRANSFERS_M
    """
    @staticmethod
    def getLastTransfers(user_id):
        max_transfers = config['N_LAST_TRANSFERS']
        annullable_time = config['T_ANNULLABLE_TRANSFERS_M']

        transfers = Transfer.objects.filter(sender=user_id)
        transfers = transfers.select_related('receiver')
        transfers = transfers.order_by('time_stamp').reverse()[:max_transfers]
        transfers = transfers.values('id', 'annullated', 'amount', 'receiver__nickname', 'time_stamp')

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        now = datetime.now()
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        for transfer in transfers:
            if time_limit > transfer['time_stamp']:
                transfer.update({'annullable': False})
            else:
                transfer.update({'annullable': True})
            transfer['receiver_nickname'] = transfer.pop('receiver__nickname')
        
        return list(transfers)

    """
    Performs the transfer routine where a sender sends money to a receiver.
    @param user_id: id of the user that wants to send money
    @param receiver_id: id of the user that should get the money
    @param amount: amount of money to be sent
    @param token: unique token got by TokenLogic's getToken
    """
    @staticmethod
    def transfer(user_id, receiver_id, amount, token):
        sender = list(User.objects.filter(id=user_id))[0]
        receiver = list(User.objects.filter(id=receiver_id))[0]
        try:
            with transaction.atomic():
                transfer_id = TransferLogic.__createTransferTuple(sender, receiver, amount, token)
                TransferLogic.__updateSenderMoney(sender, amount)
                TransferLogic.__updateReceiverMoney(receiver, amount)
        except IntegrityError:
            return list(Transfer.objects.filter(token=token))[0]
        return transfer_id

    @staticmethod
    def __createTransferTuple(sender, receiver, amount, token):
        transfer = Transfer(sender=sender, receiver=receiver, amount=amount, token=token, annullated=False)
        transfer.save()
        return transfer.id

    @staticmethod
    def __updateSenderMoney(sender, amount):
        sender.updateMoney((-1) * amount)

    @staticmethod
    def __updateReceiverMoney(receiver, amount):
        receiver.updateMoney(amount) 

    @staticmethod
    def annullateTransfer(transfer_id, token):
        annullable_time = config['T_ANNULLABLE_TRANSFERS_M']

        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        now = datetime.now()
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        transfer = list(Transfer.objects.filter(id=transfer_id))[0]
        if time_limit > transfer.time_stamp:
            raise TransferNotAnnullable()

        receiver = list(User.objects.filter(id=transfer.receiver_id))[0]
        sender = list(User.objects.filter(id=transfer.sender_id))[0]
        with transaction.atomic():
            transfer.annullate()
            receiver.updateMoney((-1) * transfer.amount)
            sender.updateMoney(transfer.amount)

