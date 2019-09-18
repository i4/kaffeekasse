from .models import *
from django.contrib.auth import login
from django.db.models import Count
from django.db.models.functions import Lower
from datetime import date, timedelta 


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
        logins = Login.objects.filter(client_id=client_id, time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        logins = logins.select_related('user')
        logins = logins.values('user__nickname', 'user__id')
        logins = logins.annotate(total=Count('user__id'))
        logins = logins.order_by('total').reverse()[:max_users]
        return list(logins)


class ProductLogic:
    
    """
    Collects the prodcuts that are most bought on one client within a given time period.
    Returns a list of dictionries on success: [{'product__name': '...', 'product_id': ..., 'total': ...}, ...]
    @param max_products: the maximum of products taht should be shown
    @param max_days: the maximum of days that have passed since the last logisince the purchase 
    """
    @staticmethod
    def getMostBoughtProductsList(max_products, max_days):
        time_stamp = date.today() - timedelta(days=max_days)
        products = Purchase.objects.filter(client_id=client_id, time_stamp__gte=time_stamp.strftime("%Y-%m-%d") + " 00:00")
        products = products.select_related('product')
        products = products.values('product__name', 'product_id')
        products = products.annotate(total=Count('product_id'))
        products = products.order_by('total').reverse()[:max_products]
        print(products.query)
        print(products)
        return list(products)
