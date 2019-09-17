from django.shortcuts import render
from .models import user, product

# Create your views here.


def index(request):
    return render(request, "index.html", {"users": user.objects.all()})


def buy(request):
    return render(request, "buy.html", {
        "drinks": product.objects.filter(category="drink"),
        "candies": product.objects.filter(category="candy"),
    })


def charge(request):
    return render(request, "charge.html", {})


def transfer(request):
    return render(request, "transfer.html", {"users": user.objects.all()})
