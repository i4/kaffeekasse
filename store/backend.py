from .models import *
from django.contrib.auth import login
from django.db.models import Count, ObjectDoesNotExist
from django.db.models.functions import Lower
from datetime import date, timedelta, datetime
from django.db import transaction, IntegrityError
from .store_config import KAFFEEKASSE as config
import pytz


class UserLogic:

    """
    Basic login function. On success the user is logged in and True is returned. On Failure nothing happens and False is
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
            login(request, user)
            return True
        return False

    """
    Collects the users that have the most log ins on a client within a given time period.
    Returns a list of dictionaries on succes: [{'user__nickname': '...', 'user__id': ..., 'total': ...}, ...]
    @config-param max_users: the maximum of users that should be shown. Depends on N_USERS_LOGIN
    @config-param max_days: the maximum of days that have passed since the last login. Depends on T_USERS_LOGIN_D
    """
    @staticmethod
    def getFrequentUsersList():
        max_users = config['N_USERS_LOGIN']
        max_days = config['T_USERS_LOGIN_D']
        time_stamp = date.today() - timedelta(days=max_days)
        logins = Login.objects.filter(time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        logins = logins.select_related('user')
        logins = logins.values('user__nickname', 'user__id')
        logins = logins.annotate(total=Count('user__id'))
        if max_users <= 0:
            logins = logins.order_by('total').reverse()
        else:
            logins = logins.order_by('total').reverse()[:max_users]
        return list(logins)


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
            if time_limit >= purchase_time:
                product.update({'annullable': False})
            else:
                product.update({'annullable': True})
        print(products)
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
        try:
            purchase = Purchase(user=user, product=product, price=product.price, token=token, annullated=False)
            purchase.save()
        except IntegrityError:
            return False, -1
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
    def annullatePurchase(purchase_id):
        # warning: summertime/wintertime currently is not respected in the following calculations. This should be
        # implemented to avoid non-annullable transactions in the lost hour between summer- and wintertime
        annullable_time = config['T_ANNULLABLE_PURCHASE_M']
        now = datetime.now()
        time_limit = datetime.now() - timedelta(minutes=annullable_time)
        timezone = pytz.timezone('Europe/Berlin')
        time_limit = timezone.localize(time_limit)

        purchase = list(Purchase.objects.filter(id=purchase_id))[0]
        purchase_time = purchase['time_stamp']
        if time_limit >= purchase_time:
            return False
        else:
            purchase.annullate()
            return True

