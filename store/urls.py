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

    # Test
    path('test', views.test, name="test"),
    path('test2', views.test2, name="test2"),
]
