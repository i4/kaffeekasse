from django.shortcuts import render, reverse
from .models import User, Product
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout as auth_logout
from .backend import *


# Rendered pages

@require_http_methods(["GET"])
def index(request):
    # TODO: Remove hard coded client id
    clientid = "0xf0x4-0x60x2-0xe0xe-0x90xe-0x70xf-0x10xb"
    return render(request, "index.html", {"users": UserLogic.getFrequentUsersList(clientid, 20, 30)})

@login_required(login_url="index")
@require_http_methods(["GET"])
def buy(request):
    return render(request, "buy.html", {
        "drinks": Product.objects.filter(category="drink"),
        "candies": Product.objects.filter(category="candy"),
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
    return HttpResponse()

# Test

def test(request):
    return render(request, "test.html", {})


def test2(request):
    GetMostFrequentUsers.getFrequentUsersList("0x50xd-0xf0x3-0x60xd-0x50x3-0xd0x9-0xb0x20x50x4-0x90x2-0xd0xd-0x20x3-0xa0x9-0x10x00x80x4-0x50x8-0xf0x6-0xb0xd-0x50xb-0x90xf",
                                              4, 4*7)
