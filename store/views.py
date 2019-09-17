from django.shortcuts import render, reverse
from .models import User, Product
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login
from .backend import *

# Create your views here.

@require_http_methods(["GET"])
def index(request):
    return render(request, "index.html", {"Users": User.objects.all()})

@require_http_methods(["GET"])
def buy(request):
    return render(request, "buy.html", {
        "drinks": Product.objects.filter(category="drink"),
        "candies": Product.objects.filter(category="candy"),
    })

@require_http_methods(["GET"])
def charge(request):
    return render(request, "charge.html", {})


@require_http_methods(["GET"])
def transfer(request):
    return render(request, "transfer.html", {"Users": User.objects.all()})

@require_http_methods(["POST"])
@csrf_protect
def login(request):
    if (LoginLogic.login(request, request.POST.get("user_id"))):
        return HttpResponseRedirect(reverse("buy"))
    else:
        return HttpResponseRedirect(reverse("index"))


def test(request):
    user = User.objects.get(pk=1)
    login(request, user)
    
    return render(request, "test.html", {})