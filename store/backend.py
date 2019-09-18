from .models import User, Client, Login
from django.contrib.auth import login
from django.db.models import Count
from django.db.models.functions import Lower


class LoginLogic:

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
    

class GetMostFrequentUsers:

    @staticmethod
    def getFrequentUsersList(client_id, max_users, max_days):
        logins = Login.objects.filter(client_id=client_id)
        logins = Login.objects.select_related('user')
        logins = logins.values('user__nickname', 'user__id')
        logins = logins.annotate(total=Count('user__id'))
        logins = logins.order_by('total').reverse()[:max_users]
        return logins
