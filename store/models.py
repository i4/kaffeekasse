import django.core.validators as validators
from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import gettext_lazy as _


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


class User(AbstractUser):
    username = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=128, null=True)
    email = models.EmailField()
    money = models.DecimalField(max_digits=6, decimal_places=2, default=0.0,
            validators=[validators.MinValueValidator(0)])
    pk_login_enabled = models.BooleanField(_("Login aus Auswahlliste"), default=True)


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

    user = models.ForeignKey('user', on_delete=models.CASCADE)
    ident_type = models.IntegerField(choices=choices)
    ident = models.TextField()


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


class Charge(models.Model):
    user = models.ForeignKey('user', on_delete=models.CASCADE)
    time_stamp = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2,
            validators=[validators.MinValueValidator(0)])
    annullated = models.BooleanField()


class Purchase(models.Model):
    user = models.ForeignKey('user', on_delete=models.CASCADE)
    product = models.ForeignKey('product', on_delete=models.SET_NULL,
            null=True)
    time_stamp = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=6, decimal_places=2,
            validators=[validators.MinValueValidator(0)])
    annullated = models.BooleanField()


class Transfer(models.Model):
    sender = models.ForeignKey('user', on_delete=models.SET_NULL, null=True,
            related_name='sender')
    receiver  = models.ForeignKey('user', on_delete=models.SET_NULL,
            null=True, related_name='receiver')
    time_stamp = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2,
            validators=[validators.MinValueValidator(0)])
    annullated = models.BooleanField()


class Login(models.Model):
    time_stamp = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE)
