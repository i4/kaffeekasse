from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, "index.html", {})


def buy(request):
    return render(request, "buy.html", {})


def charge(request):
    return render(request, "charge.html", {})


def transfer(request):
    return render(request, "transfer.html", {})
