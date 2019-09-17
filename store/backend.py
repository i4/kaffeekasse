from .models import User
from django.contrib.auth import login


class LoginLogic:

    @staticmethod
    def login(request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExcist:
            user = None
        if user is not None:
            login(request, user)
            return True
        return False


