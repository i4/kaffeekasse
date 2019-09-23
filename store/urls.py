from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('buy', views.buy, name='buy'),
    path('buy_revert', views.buy_revert, name='buy_revert'),
    path('transfer', views.transfer, name='transfer'),
    path('transfer_revert', views.transfer_revert, name='transfer_revert'),
    path('charge', views.charge, name="charge"),
    path('charge_revert', views.charge_revert, name='charge_revert'),

    # Auth
    path('login', views.login, name="login"),
    path('logout', views.logout, name="logout"),

    # At-most-once token
    path('token', views.getToken, name="getToken"),

    # Test
    path('stresstest', views.stressTest, name="stresstest"),
    path('test2', views.test2, name="test2"),
]
