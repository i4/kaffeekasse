from .models import *
from django.contrib.auth import login
from django.db.models import Count
from django.db.models.functions import Lower
from datetime import date, timedelta 
from django.db import transaction, IntegrityError


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
    @param max_users: the maximum of users that should be shown
    @param max_days: the maximum of days that have passed since the last login
    """
    @staticmethod
    def getFrequentUsersList(max_users, max_days):
        time_stamp = date.today() - timedelta(days=max_days)
        logins = Login.objects.filter(time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        logins = logins.select_related('user')
        logins = logins.values('user__nickname', 'user__id')
        logins = logins.annotate(total=Count('user__id'))
        logins = logins.order_by('total').reverse()[:max_users]
        return list(logins)


class ProductLogic:
    
    """
    Collects the prodcuts that are most bought within a given time period.
    Returns a list of dictionries on success: [{'product__name': '...', 'product_id': ...,  'product__price': ..., 'total': ...}, ...]
    @param max_products: the maximum of products that should be shown
    @param max_days: the maximum of days that have passed since the last logisince the purchase 
    """
    @staticmethod
    def getMostBoughtProductsList(max_products, max_days):
        time_stamp = date.today() - timedelta(days=max_days)
        products = Purchase.objects.filter(time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        products = products.select_related('product')
        products = products.values('product__name', 'product_id', 'product__price')
        products = products.annotate(total=Count('product_id'))
        products = products.order_by('total').reverse()[:max_products]
        return list(products)

    """
    Collects the products that are most bought by one user.
    Returns a list of dictionaries on success: [{'product__name': '...', 'product_id': 41, 'product__price': ...}]
    @param user_id: the id of the user
    @param max_products: the maximum of products that should be shown
    """
    @staticmethod
    def getLastBoughtProductsList(user_id, max_products):
        products = Purchase.objects.filter(user=user_id)
        products = products.select_related('product')
        products = products.order_by('time_stamp').reverse()[:max_products]
        products = products.values('product__name', 'product_id', 'product__price')
        print(products)
        print(products.query)
        return list(products)


class TokenLogic:

    @transaction.atomic
    def get_token(self):
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
    @transaction.atomic
    def purchase(self, user_id, product_id, token):
        user = list(User.objects.filter(id=user_id))[0]
        product = list(Product.objects.filter(id=product_id))[0]

        if not self.__createPurchaseTuple(user, product, token):
            return False
        self.__updateUserMoney(user, product.price)
        self.__updateProductStock(product)
        return True

    def __createPurchaseTuple(self, user, product, token):
        try:
            purchase = Purchase(user=user, product=product, price=product.price, token=token, annulated=False)
            purchase.save()
        except IntegrityError:
            return False
        return True

    def __updateUserMoney(self, user, price):
        user.updateMoney(price * (-1)) 

    def __updateProductStock(self, product):
        product.updateStock(-1) 

