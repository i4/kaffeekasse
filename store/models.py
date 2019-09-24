from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from decimal import Decimal
from .store_exceptions import *


class User(AbstractUser):
    username = models.TextField(null=False, unique=True)
    password = models.TextField(null=True)
    email = None
    money = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    def incrementMoney(self, amount):
        if amount < 0:
            raise NegativeMoneyAmount()
        self.money += Decimal(amount)
        self.save()
        return True

    def decrementMoney(self, amount):
        if amount < 0:
            raise NegativeMoneyAmount()
        if self.money - amount < 0:
            raise UserNotEnoughMoney()
        self.money -= Decimal(amount)
        self.save()
        return True
        

class Product(models.Model):
    name = models.TextField(null=False)
    category = models.TextField(null=False)
    stock = models.IntegerField(null=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def updateStock(self, amount):
        self.stock += amount
        self.save()
        return True


class Charge(models.Model):
    token = models.BigIntegerField(null=False, unique=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE, null=False)
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    annullated = models.BooleanField(null=False) 

    def annullate(self):
        self.annullated = True
        self.save()


class Purchase(models.Model):
    token = models.BigIntegerField(null=False, unique=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE, null=False)
    product = models.ForeignKey('product', on_delete=models.SET_NULL,
            null=True)
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    annullated = models.BooleanField(null=False)

    def annullate(self):
        self.annullated = True
        self.save()


class Transfer(models.Model):
    token = models.BigIntegerField(null=False, unique=True)
    sender = models.ForeignKey('user', on_delete=models.SET_NULL, null=True,
            related_name='sender')
    receiver  = models.ForeignKey('user', on_delete=models.SET_NULL,
            null=True, related_name='receiver')
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    annullated = models.BooleanField(null=False)

    def annullate(self):
        self.annullated = True
        self.save()


class Login(models.Model):
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    user  = models.ForeignKey('user', on_delete=models.CASCADE, null=False)


class Token(models.Model):
    token = models.BigIntegerField(unique=True, default=0)

    def increment(self):
        self.token += 1
        self.save()

