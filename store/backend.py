from .models import User, Client, Login
from django.contrib.auth import login
from django.db.models import Sum


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
        # logins = Login.objects.filter(client=client_id).select_related()
        logins = Login.objects.filter(client=client_id).prefetch_related('user')
        # logins = logins.values('nickname').annotate(Sum('user'))
        doc = open("./testlog.out", "w")
        for login in logins:
            # doc.write(login.user.nickname + " " + str(login['user__sum']) + "\n")
            doc.write(login.user.nickname)
        doc.close()

