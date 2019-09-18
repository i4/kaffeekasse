from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


class User(AbstractBaseUser):
    firstname = models.TextField(null=False)
    surname = models.TextField(null=False)
    nickname = models.TextField()
    money = models.DecimalField(max_digits=6, decimal_places=2)
    password = models.TextField(null=True)
    USERNAME_FIELD = 'id'

class Product(models.Model):
    name = models.TextField(null=False)
    category = models.TextField(null=False)
    stock = models.IntegerField(null=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)

class Charge(models.Model):
    id = models.TextField(primary_key=True)
    token = models.BigIntegerField(null=False, unique=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE, null=False)
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

class Purchase(models.Model):
    id = models.TextField(primary_key=True)
    token = models.BigIntegerField(null=False, unique=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE, null=False)
    product = models.ForeignKey('product', on_delete=models.SET_NULL,
            null=True)
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

class Transfer(models.Model):
    id = models.TextField(primary_key=True)
    token = models.BigIntegerField(null=False, unique=True)
    sender = models.ForeignKey('user', on_delete=models.SET_NULL, null=True,
            related_name='sender')
    receiver  = models.ForeignKey('user', on_delete=models.SET_NULL,
            null=True, related_name='receiver')
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

class Login(models.Model):
    id = models.TextField(primary_key=True)
    time_stamp = models.DateTimeField(null=False, auto_now=True)
    user  = models.ForeignKey('user', on_delete=models.CASCADE, null=False)

class Token(models.Model):
    token = models.BigIntegerField(primary_key=True, default=0)

