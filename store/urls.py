from django.urls import path

from . import views

urlpatterns = [
    # Views
    path('', views.index, name='index'),
    path('buy', views.buy, name='buy'),
    path('transfer', views.transfer, name='transfer'),
    path('charge', views.charge, name="charge"),

    # Auth
    path('login', views.login, name="login"),
    path('logout', views.logout, name="logout"),

    # API
    path('buy_product', views.buyProduct, name="buy_product"),
    path('token', views.getToken, name="getToken"),
    path('revert_purchase', views.revert_purchase, name="revert_purchase"),
    path('charge_money', views.charge_money, name="charge_money"),
    path('revert_charge', views.revert_charge, name="revert_charge"),

    # Test
    path('test', views.test, name="test"),
    path('test2', views.test2, name="test2"),
]
