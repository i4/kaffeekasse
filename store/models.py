from django.db import models


class user(models.model):
    firstname = models.TextField()
    surname = models.TextField()
    nickname = models.TextField()
    money = models.DecimalField(max_digits=6, decimal_places=2)
