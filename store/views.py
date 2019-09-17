from django.shortcuts import render
from .models import user

# Create your views here.


def index(request):
    return render(request, "index.html", {"users": user.objects.all()})


def buy(request):
    return render(request, "buy.html", {})


def charge(request):
    return render(request, "charge.html", {})


def transfer(request):
    return render(request, "transfer.html", {"users": user.objects.all()})
