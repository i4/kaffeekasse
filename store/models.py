from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from decimal import Decimal
from .store_exceptions import *
from django.utils.translation import gettext_lazy as _



class User(AbstractUser):
    username = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=128, null=True)
    email = models.EmailField(null=True, blank=True)
    money = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    pk_login_enabled = models.BooleanField(_("Login aus Auswahlliste"), default=True)

    def incrementMoney(self, amount):
        if amount < 0:
            raise NegativeMoneyAmount()
        self.money += Decimal(amount)
        self.save()

    def decrementMoney(self, amount):
        if amount < 0:
            raise NegativeMoneyAmount()
        if self.money - amount < 0:
            raise UserNotEnoughMoney()
        self.money -= Decimal(amount)
        self.save()


class UserIdentifier(models.Model):
    PRIMARYKEY = 0
    ID = 1
    BARCODE = 2
    RFID = 3

    choices = [
        (PRIMARYKEY, 'Pk'),
        (ID, 'Id'),
        (BARCODE, 'Barcode'),
        (RFID, 'RFID'),
    ]

    user = models.ForeignKey('user', on_delete=models.CASCADE)
    ident_type = models.IntegerField(choices=choices)
    ident = models.TextField()


class Product(models.Model):
    name = models.TextField()
    category = models.ForeignKey('productcategory', on_delete=models.CASCADE, related_name="products")
    stock = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def updateStock(self, amount):
        self.stock += amount
        self.save()


class ProductCategory(models.Model):
    SNACK = 0
    GETRAENK = 1

    choices = [
        (SNACK, 'Snack'),
        (GETRAENK, 'Drink'),
    ]

    toplevel = models.IntegerField(_("Toplevel category"), choices=choices)
    sublevel = models.TextField(_("Sublevel category"), unique=True)


class ProductIdentifier(models.Model):
    ID = 0
    BARCODE = 1
    PRIMARYKEY = 2

    choices = [
        (ID, 'Id'),
        (BARCODE, 'Barcode'),
        (PRIMARYKEY, 'Pk'),
    ]

    product = models.ForeignKey('product', on_delete=models.CASCADE)
    ident_type = models.IntegerField(choices=choices)
    ident = models.TextField()


class Charge(models.Model):
    token = models.BigIntegerField(unique=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE)
    time_stamp = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    annullated = models.BooleanField()

    def annullate(self):
        self.annullated = True
        self.save()


class Purchase(models.Model):
    token = models.BigIntegerField(unique=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE)
    product = models.ForeignKey('product', on_delete=models.SET_NULL,
            null=True)
    time_stamp = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    annullated = models.BooleanField()

    def annullate(self):
        self.annullated = True
        self.save()


class Transfer(models.Model):
    token = models.BigIntegerField(unique=True)
    sender = models.ForeignKey('user', on_delete=models.SET_NULL, null=True,
            related_name='sender')
    receiver  = models.ForeignKey('user', on_delete=models.SET_NULL,
            null=True, related_name='receiver')
    time_stamp = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    annullated = models.BooleanField()

    def annullate(self):
        self.annullated = True
        self.save()


class Login(models.Model):
    time_stamp = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE)


class Token(models.Model):
    token = models.BigIntegerField(unique=True, default=0)

    def increment(self):
        self.token += 1
        self.save()
