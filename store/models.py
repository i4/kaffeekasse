from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class User(AbstractBaseUser):
    firstname = models.TextField(null=False)
    surname = models.TextField(null=False)
    nickname = models.TextField()
    money = models.DecimalField(max_digits=6, decimal_places=2)
    password = models.TextField(null=True)
    USERNAME_FIELD = 'id'

class client(models.Model):
    mac = models.TextField(primary_key=True)

class product(models.Model):
    name = models.TextField(null=False)
    category = models.TextField(null=False)
    stock = models.IntegerField(null=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)

class charge(models.Model):
    id = models.TextField(primary_key=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE, null=False)
    client = models.ForeignKey('client', on_delete=models.SET_NULL, null=True)
    time_stamp = models.TimeField(null=False, auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

class purchase(models.Model):
    id = models.TextField(primary_key=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE, null=False)
    product = models.ForeignKey('product', on_delete=models.SET_NULL,
            null=True)
    client = models.ForeignKey('client', on_delete=models.SET_NULL, null=True)
    time_stamp = models.TimeField(null=False, auto_now=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

class transfer(models.Model):
    id = models.TextField(primary_key=True)
    sender = models.ForeignKey('user', on_delete=models.SET_NULL, null=True,
            related_name='sender')
    receiver  = models.ForeignKey('user', on_delete=models.SET_NULL,
            null=True, related_name='receiver')
    client  = models.ForeignKey('client', on_delete=models.SET_NULL, null=True)
    time_stamp = models.TimeField(null=False, auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

class login(models.Model):
    id = models.TextField(primary_key=True)
    time_stamp = models.TimeField(null=False, auto_now=True)
    user  = models.ForeignKey('user', on_delete=models.CASCADE, null=False)
    client  = models.ForeignKey('client', on_delete=models.SET_NULL, null=True)
