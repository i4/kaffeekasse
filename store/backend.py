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

    @staticmethod
    def getUser(identifier, identifier_type):
        idf = UserIdentifier.objects.filter(identifier=identifier, identifier_type=identifier_type)
        idf = idf.select_related('user')
        idf = list(idf)
        if len(idf) == 0:
            raise UserIdentifierNotExists()
        idf = idf[0]
        user = idf.user
        if not user.pk_login_enabled:
            raise DisabledIdentifier()
        return user


    @staticmethod
    def login(request, identifier, identifier_type):
        """
        Basic login function. On success the user is logged in and True is returned and a login-tuple is created. On Failure nothing happens and False is
        returned.
        @param request: the request object
        @param user_id: id of the user that should log in
        """
        user = UserLogic.getUser(identifier, identifier_type)
        with transaction.atomic():
            login_tuple = Login(user=user)
            login_tuple.save()
            login(request, user)


    @staticmethod
    def getFrequentUsersList():
        """
        Concatinates the results of three db-queries:
        First part of the list: a number of users specified in max_users, that have most logins within a number of days
        specified in max_days.
        Second part of the list: all users that are not included in the first part of the list and have at least one login
        Third part of the list: all users that are not included in the firt both parts
        Returned list: [{'user': ..., 'user_username': ..., 'total': ...}]
        @config-param max_users: depends on N_USERS_LOGIN
        @config-param max_days: depends on T_USERS_LGIN_D
        """
        max_users = config['N_USERS_LOGIN']
        max_days = config['T_USERS_LOGIN_D']
        time_stamp = date.today() - timedelta(days=max_days)

        recent_logins = Login.objects.filter(time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        recent_logins = recent_logins.select_related('user')
        recent_logins = recent_logins.filter(user__pk_login_enabled=True)
        recent_logins = recent_logins.values('user__username', 'user__id')
        recent_logins = recent_logins.annotate(total=Count('user__id'))
        if max_users <= 0:
            recent_logins = recent_logins.order_by('total').reverse()
        else:
            recent_logins = recent_logins.order_by('total').reverse()[:max_users]

        old_logins = Login.objects.all()
        old_logins = old_logins.select_related('user')
        old_logins = old_logins.filter(user__pk_login_enabled=True)
        old_logins = old_logins.values('user__username', 'user__id')
        old_logins = old_logins.exclude(user__id__in=[d['user__id'] for d in list(recent_logins)])
        old_logins = old_logins.annotate(total=Count('user__id'))
        old_logins = old_logins.order_by('total').reverse()

        no_logins = User.objects.filter(pk_login_enabled=True).exclude(id__in=[d['user__id'] for d in list(recent_logins) + list(old_logins)])
        no_logins = no_logins.order_by('username')
        no_logins = no_logins.values('username', 'id')
        no_logins = no_logins.annotate(total=Count('id'))

        for login in no_logins:
            login['user__id'] = login.pop('id')
            login['user__username'] = login.pop('username')
            login['total'] = 0

        return list(recent_logins) + list(old_logins) + list(no_logins)


class ProductLogic:

    @staticmethod
    def getProduct(identifier, identifier_type):
        print(identifier, identifier_type)
        if int(identifier_type) == 2:
            products = list(Product.objects.filter(id=int(identifier)))
            print("products:", products)
            if len(products) == 0:
                raise ProductIdentifierNotExists()
            product = products[0]
            return product
        else:
            idf = ProductIdentifier.objects.filter(identifier_type=identifier_type).filter(identifier=identifier)
            idf = idf.select_related('product')
            idf = list(idf)
            if len(idf) == 0:
                raise ProductIdentifierNotExists()
            idf = idf[0]
            product = idf.product
        return product


    @staticmethod
    def getMostBoughtProductsList():
        """
        Result of a db query asking for a number of products specified in max_products that were most bought within the
        last max_days number of days.
        Returned list: [{'product__name': ..., 'product_id': ..., 'product__price': ...,'total': ...}]
        @config-param max_products: depends on N_MOST_BOUGHT_PRODUCTS
        @config-param max_days: depends on T_MOST_BOUGHT_PRODUCTS_D
        """
        max_products = config['N_MOST_BOUGHT_PRODUCTS']
        max_days = config['T_MOST_BOUGHT_PRODUCTS_D']
        time_stamp = date.today() - timedelta(days=max_days)
        products = Purchase.objects.filter(time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        products = products.select_related('product')
        products = products.values('product__name', 'product_id', 'product__price')
        products = products.annotate(total=Count('product_id'))
        products = products.order_by('total').reverse()[:max_products]
        return list(products)

    @staticmethod
    def getLastBoughtProductsList(user_id):
        """
        Resulst of a db query asking for a number of products specified in max_products that were recently bought by a
        specified user. The result also contains information on the state of a possible annullation of the products
        purchase.
        Returned list: [{'product__name': ..., 'product_id': ..., 'product__price': ..., 'time_stamp': ..., 'id': ...,
        'annullated': ..., 'annullable': ...}]
        @param user_id: id of the specified user
        @config-param max_products: depends on N_ANNULLABLE_PURCHASE
        @config-param annullable_time: depends on T_ANNULLABLE_PURCHASE_M
        """
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

    @staticmethod
    def getProductByCategory(category):
        """
        Returns a dict with a key for each sublevel category containing all products, where the toplevel category equals to the input category
        @param category: Toplevel category (Use enum ToplevelProductCategories)
        """
        # Get sublevels
        sublevels = ProductCategory.objects.filter(toplevel=category).values('sublevel')

        # Get product
        products = {}
        for sublevel in sublevels:
            # Get product for sublevel
            sublevel = sublevel["sublevel"]
            ps = ProductCategory.objects.filter(toplevel=category, sublevel=sublevel).prefetch_related('products').values('products__id', 'products__name', 'products__price').all()

            # Rename keys
            for p in ps:
                p['id'] = p.pop('products__id')
                p['name'] = p.pop('products__name')
                p['price'] = p.pop('products__price')

            products[sublevel] = list(ps)

        return products

    @staticmethod
    def getCandies():
        return ProductLogic.getProductByCategory(ToplevelProductCategories.SNACK)

    @staticmethod
    def getDrinks():
        return ProductLogic.getProductByCategory(ToplevelProductCategories.GETRAENK)


class TokenLogic:

    @staticmethod
    def get_token():
        """
        Generates a new and unique token as 64-bit integer to be used in a at-most-once client-server-interaction.
        """
        with transaction.atomic():
            token = list(Token.objects.all())[0]
            token.increment()
            return token.token


class PurchaseLogic:

    @staticmethod
    def purchase(user_id, product_identifier, product_identifier_type, token):
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
        try:
            with transaction.atomic():
                user = list(User.objects.filter(id=user_id))[0]
                product = ProductLogic.getProduct(product_identifier, product_identifier_type)
                purchase_create_return_tuple = PurchaseLogic.__createPurchaseTuple(user, product, token)
                PurchaseLogic.__updateUserMoney(user, product.price)
                PurchaseLogic.__updateProductStock(product)
        except ObjectDoesNotExist:
            print("ObjectDoesNotExist")
            return -1
        except ProductIdentifierNotExists:
            print("ProductIdentifierNotExists")
            return -1
        except IntegrityError:
            print("IntegrityError")
            purchase = list(Purchase.objects.filter(token=token))[0], product.id
            return purchase.id
        return purchase_create_return_tuple[1], product.id

    @staticmethod
    def __createPurchaseTuple(user, product, token):
        purchase = Purchase(user=user, product=product, price=product.price, token=token, annullated=False)
        purchase.save()
        return True, purchase.id

    @staticmethod
    def __updateUserMoney(user, price):
        user.decrementMoney(price)

    @staticmethod
    def __updateProductStock(product):
        product.updateStock(-1)

    @staticmethod
    def annullatePurchase(purchase_id, token):
        """
        Try to annullate a purchase performed by a specified user. THis will only fail if the purchase was performed too
        long ago.
        @param purchase_id: id of the purchase to be annullated
        @param token: token received by tokenLogics get_token
        @conifg-param annullable_time: depends on T_ANNULLABLE_PURCHASE_M
        """
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
            user.incrementMoney(purchase.price)


class ChargeLogic:

    @staticmethod
    def getLastChargesList(user_id):
        """
        Result of a db query asking for a number of charges specified in max_charges that were recently performed by a
        specified user. The result also contains information on the state of a possible annullation of the charge.
        Returned list: [{'id': ..., 'amount': ..., 'annullated': ..., 'time_stamp': ..., 'annullable': ...}]
        @param user_id: id of the specified user
        @config-param max_charges: depends on N_ANNULLABLE_CHARGES
        @config-param annullable_time: depends on T_ANNULLABLE_CHARGE_M
        """
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

    @staticmethod
    def charge(user_id, amount, token):
        """
        Executes the charge logic.
        @param user_id: id of the user that charges
        @param amount: the amount of money to be charged
        @param token: the unique token got by getToken()
        """
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
        user.incrementMoney(amount)

    @staticmethod
    def annullateCharge(charge_id, token):
        """
        Try to annullate a charge performed by a specified user. This will fail if either the charge was performed too
        long ago or the user has less money on it's account than the amount of money charged.
        @param charge_id: id of the charge to be annullated
        @param token: token received by tokenLogics get_token
        @conifg-param annullable_time: depends on T_ANNULLABLE_CHARGE_M
        """
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
            user.decrementMoney(charge.amount)


class TransferLogic:
    @staticmethod
    def getFreuquentTransferTargeds(user_id):
        """
        Result of a db query asking for a number of receivers specified in max_receivers that are often addresed by a specified user
        Returned list: [{'receiver': ..., 'username': ...}]
        @param user_id: id of the specified user
        @config-param max_receivers: depends on N_TRANSFER_RECEIVERS
        """
        max_receivers = config['N_TRANSFERS_RECEIVERS']
        transfers = Transfer.objects.filter(sender=user_id).exclude(receiver=None)
        transfers = transfers.select_related('receiver')
        transfers = transfers.values('receiver', 'receiver__username')
        transfers = transfers.annotate(total=Count('receiver'))
        transfers = transfers.order_by('receiver__username').order_by('total').reverse()
        if max_receivers >= 0:
            transfers = transfers[:max_receivers]

        for transfer in transfers:
            transfer['id'] = transfer.pop('receiver')
            transfer['username'] = transfer.pop('receiver__username')

        return list(transfers)

    @staticmethod
    def getLastTransfers(user_id):
        """
        Result of a db query asking for a number of transfers that have been recently performed by a specified user. Also
        returns information on the state of possible annullation of the transfer.
        Returned list: [{'id': ..., 'annullated': ..., 'amount': ..., 'receiver_username': ..., 'time_stamp': ...,
        'annullable': ...}]
        @param user_id: id of the specified user
        @config-param max_transfers: depends on N_LAST_TRANSFERS
        @config-param annullable_time: depends on T_ANNULLABLE_TRANSFERS_M
        """
        max_transfers = config['N_LAST_TRANSFERS']
        annullable_time = config['T_ANNULLABLE_TRANSFERS_M']

        transfers = Transfer.objects.filter(sender=user_id)
        transfers = transfers.select_related('receiver')
        transfers = transfers.order_by('time_stamp').reverse()[:max_transfers]
        transfers = transfers.values('id', 'annullated', 'amount', 'receiver__username', 'time_stamp')

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
            transfer['receiver_username'] = transfer.pop('receiver__username')

        return list(transfers)

    @staticmethod
    def transfer(user_id, receiver_id, amount, token):
        """
        Performs the transfer routine where a sender sends money to a receiver.
        @param user_id: id of the user that wants to send money
        @param receiver_id: id of the user that should get the money
        @param amount: amount of money to be sent
        @param token: unique token got by TokenLogic's getToken
        """
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
        sender.decrementMoney(amount)

    @staticmethod
    def __updateReceiverMoney(receiver, amount):
        receiver.incrementMoney(amount)

    @staticmethod
    def annullateTransfer(transfer_id, token):
        """
        Try to annullate a transfer performed by a specified user. This will fail if either the transfer was performed too
        long ago or the receiver of the money has less money on it's account than the amount of money transfered.
        @param transfer_id: id of the transfer to be annullated
        @param token: token received by tokenLogics get_token
        @conifg-param annullable_time: depends on T_ANNULLABLE_TRANSFERS_M
        """
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
            receiver.decrementMoney(transfer.amount)
            sender.incrementMoney(transfer.amount)

