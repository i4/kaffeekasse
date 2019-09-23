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

    # At-most-once token
    path('token', views.getToken, name="getToken"),

    # Test
    path('stresstest', views.stressTest, name="stresstest"),
    path('test2', views.test2, name="test2"),
]
