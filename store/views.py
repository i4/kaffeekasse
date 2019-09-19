from django.shortcuts import render, reverse
from .models import User, Product
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import logout as auth_logout
from .backend import *


# Rendered pages

@require_http_methods(["GET"])
def index(request):
    # TODO: Remove hard coded client id
    return render(request, "index.html", {"users": UserLogic.getFrequentUsersList(20, 30)})


@login_required(login_url="index")
@require_http_methods(["GET"])
def buy(request):
    return render(request, "buy.html", {
        "most_bought": ProductLogic.getMostBoughtProductsList(5, 30),
        "drinks": Product.objects.filter(category="drink"),
        "candies": Product.objects.filter(category="candy"),
        "products": Product.objects.all(),
    })


@login_required(login_url="index")
@require_http_methods(["GET"])
def charge(request):
    return render(request, "charge.html", {})


@login_required(login_url="index")
@require_http_methods(["GET"])
def transfer(request):
    return render(request, "transfer.html", {"Users": User.objects.all()})


# Authentication

@require_http_methods(["POST"])
@csrf_protect
def login(request):
    if (UserLogic.login(request, request.POST.get("user_id"))):
        return HttpResponseRedirect(reverse("buy"))
    else:
        return HttpResponseRedirect("/store/")


@login_required(login_url="index")
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse("index"))


# API

@login_required(login_url="index")
@require_http_methods(["POST"])
def buyProduct(request):
    # TODO: Add backend logic
    user_id = request.user.id
    product_id = request.POST.get("product_id")
    token = request.POST.get("token")
    if (PurchaseLogic().purchase(user_id, product_id, token)):
        return HttpResponse()
    else:
        return HttpResponse()
    return HttpResponse()


@login_required(login_url="index")
@require_http_methods(["POST"])
def getToken(request):
    token = TokenLogic().get_token()
    return JsonResponse({"token": token})

# Test


def test(request):
    return render(request, "test.html", {})


def test2(request):
    tl = TokenLogic()
    token = tl.get_token()
    pl = PurchaseLogic()
    pl.purchase(1, 1, token)
