# SPDX-License-Identifier: GPL-3.0-or-later

import django.core.validators as validators
import django.contrib.auth.models
import django.dispatch
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.utils.translation import gettext_lazy as _

import store.config as config


# Per default, Django does not execute validators when saving a model. Enforce
# this to guarantee the code cannot break these assumptions.
#
# Used, among others, to prevent negative money for users!
def validate_model(sender, instance, raw, **kwargs):
    if not raw:
        # TODO: Find a better solution for this workaround
        # Prevent the following error "django.core.exceptions.ValidationError:
        # {'session_key': ['Session with this Session key already exists.']}"
        if not isinstance(instance, Session):
            instance.full_clean()
pre_save.connect(validate_model)


class UserData(models.Model):
    # "user" is confusing because it creates queries like "user__user__id" and
    # so on, instead use "auth" because that's its main use
    auth = models.OneToOneField(django.contrib.auth.models.User,
            on_delete=models.CASCADE)
    idm = models.CharField(max_length=8, blank=True)
    money = models.DecimalField(max_digits=6, decimal_places=2, default=0.0,
            validators=[validators.MinValueValidator(config.MONEY_MIN_LIMIT)])
    shown_on_login_screen = models.BooleanField(default=True)

    def __str__(self):
        return '{} ({} {} {})'.format(self.auth.username, self.idm,
                self.auth.first_name, self.auth.last_name)

# Automatically create a corresponding UserData object when creating a new
# User; inspired by the following post
# https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
@django.dispatch.receiver(post_save, sender=django.contrib.auth.models.User)
def post_create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            instance.userdata
        except django.contrib.auth.models.User.userdata.RelatedObjectDoesNotExist:
            UserData.objects.create(auth=instance)


class UserIdentifier(models.Model):
    # Random numbers for easy grepping
    PRIMARYKEY = 136940
    ID = 136941
    BARCODE = 136942
    RFID = 136943

    choices = [
        # NOTE: Don't list PRIMARYKEY here, it's not stored in UserIdentifier
        # but only controls using the user's primary key (as stored in User)
        # as identifier.
        (ID, 'Id'),
        (BARCODE, 'Barcode'),
        (RFID, 'RFID'),
    ]

    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    ident_type = models.IntegerField(choices=choices)
    ident = models.TextField()

    class Meta:
        constraints = [models.UniqueConstraint(name='unique_user_ident',
            fields=['ident_type', 'ident'])]


class UnknownUserIdentifier(models.Model):
    ident_type = models.IntegerField(choices=UserIdentifier.choices)
    ident = models.TextField()
    time_stamp = models.DateTimeField(auto_now=True)


class Product(models.Model):
    name = models.TextField()
    category = models.ForeignKey('productcategory', on_delete=models.CASCADE,
            related_name="products")
    stock = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2,
            validators=[validators.MinValueValidator(0)])

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    SNACK = 231740
    GETRAENK = 231741

    choices = [
        (SNACK, 'Snack'),
        (GETRAENK, 'Drink'),
    ]

    toplevel = models.IntegerField(_("Toplevel category"), choices=choices)
    sublevel = models.TextField(_("Sublevel category"), unique=True)

    def __str__(self):
        for x in ProductCategory.choices:
            if x[0] == self.toplevel:
                toplevel = x[1]
        return '{}: {}'.format(toplevel, self.sublevel)


class ProductIdentifier(models.Model):
    ID = 329310
    BARCODE = 329311
    PRIMARYKEY = 329312

    choices = [
        # NOTE: Don't list PRIMARYKEY here, it's not stored in
        # ProductIdentifier.
        (ID, 'Id'),
        (BARCODE, 'Barcode'),
    ]

    product = models.ForeignKey('product', on_delete=models.CASCADE)
    ident_type = models.IntegerField(choices=choices)
    ident = models.TextField()

    class Meta:
        constraints = [models.UniqueConstraint(name='unique_product_ident',
            fields=['ident_type', 'ident'])]


class Charge(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    time_stamp = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    annulled = models.BooleanField(default=False)
    comment = models.TextField(blank=True)


class Purchase(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    product = models.ForeignKey('product', on_delete=models.SET_NULL,
            null=True)
    time_stamp = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=6, decimal_places=2,
            validators=[validators.MinValueValidator(0)])
    annulled = models.BooleanField(default=False)


class Transfer(models.Model):
    sender = models.ForeignKey(UserData, on_delete=models.SET_NULL, null=True,
            related_name='sender')
    receiver  = models.ForeignKey(UserData, on_delete=models.SET_NULL,
            null=True, related_name='receiver')
    time_stamp = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2,
            validators=[validators.MinValueValidator(0)])
    annulled = models.BooleanField(default=False)
