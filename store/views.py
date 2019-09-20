from django.shortcuts import render, reverse
from .models import User, Product
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import logout as auth_logout
from .backend import *
from .store_exceptions import *


# Rendered pages

@require_http_methods(["GET"])
def index(request):
    # TODO: Remove hard coded client id
    return render(request, "index.html", {"users": UserLogic.getFrequentUsersList()})


@login_required(login_url="index")
@require_http_methods(["GET"])
def buy(request):
    return render(request, "buy.html", {
        "most_bought": ProductLogic.getMostBoughtProductsList(),
        "recently_bought": ProductLogic.getLastBoughtProductsList(request.user.id),
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
    try:
        purchase_return_tuple = PurchaseLogic().purchase(user_id, product_id, token)
    except UserNotEnoughMoney as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    if purchase_return_tuple >= 0:
        return JsonResponse({"purchase_id": purchase_return_tuple})
    else:
        return HttpResponse(status=400)


@login_required(login_url="index")
@require_http_methods(["POST"])
def getToken(request):
    token = TokenLogic.get_token()
    return JsonResponse({"token": token})


@login_required(login_url="index")
@require_http_methods(["POST"])
def revert_purchase(request):
    purchase_id = request.POST.get("purchase_id")
    try:
        PurchaseLogic.annullatePurchase(purchase_id)
    except PurchaseNotAnnullable as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url="index")
@require_http_methods(["POST"])
def revert_charge(request):
    charge_id = request.POST.get("charge_id")
    try:
        ChargeLogic.annullateCharge(charge_id)
    except ChargeNotAnnullable as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


# Test


def test(request):
    return render(request, "test.html", {})


def test2(request):
    ChargeLogic.annullateCharge(1900)
