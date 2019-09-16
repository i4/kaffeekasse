from django.db import models


class user(models.Model):
    firstname = models.TextField(null=False)
    surname = models.TextField(null=False)
    nickname = models.TextField()
    money = models.DecimalField(max_digits=6, decimal_places=2)

class client(models.Model):
    mac = models.TextField(primary_key=True)

class product(models.Model):
    name = models.TextField(null=False)
    category = models.TextField(null=False)
    stock = models.IntegerField(null=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)
