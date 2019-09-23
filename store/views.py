from django.shortcuts import render, reverse
from .models import User, Product
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import logout as auth_logout
from .backend import *
from .store_exceptions import *
from .stresstest import *


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
    return render(request, "charge.html", {
        "recent_charges": ChargeLogic.getLastChargesList(request.user.id),
    })


@login_required(login_url="index")
@require_http_methods(["GET"])
def transfer(request):
    return render(request, "transfer.html", {
        "users": TransferLogic.getFreuquentTransferTargeds(request.user.id),
        "recent_transfers": TransferLogic.getLastTransfers(request.user.id),
        })

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
    token = request.POST.get("token")
    try:
        PurchaseLogic.annullatePurchase(purchase_id, token)
    except PurchaseNotAnnullable as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url="index")
@require_http_methods(["POST"])
def charge_money(request):
    user_id = request.user.id
    token = request.POST.get("token")
    amount = request.POST.get("amount")
    amount = Decimal(amount)
    charge_id = ChargeLogic.charge(user_id, amount, token)
    return JsonResponse({'charge_id': charge_id})


@login_required(login_url="index")
@require_http_methods(["POST"])
def revert_charge(request):
    charge_id = request.POST.get("charge_id")
    token = request.POST.get("token")
    try:
        ChargeLogic.annullateCharge(charge_id, token)
    except ChargeNotAnnullable as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


def transfer_money(request):
    print(request.POST)
    user_id = request.user.id
    token = request.POST.get("token")
    receiver_id = request.POST.get("receiver")
    amount = Decimal(request.POST.get("amount"))
    transfer_id = TransferLogic.transfer(user_id, receiver_id, amount, token)
    return JsonResponse({"transfer_id": transfer_id})


def revert_transfer(request):
    transfer_id = request.POST.get('transfer_id')
    token = request.POST.get('token')
    try:
        TransferLogic.annullateTransfer(transfer_id, token)
    except TransferNotAnnullable as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


# Test


def stressTest(request):
    nthreads = 10
    barrier = Barrier(nthreads + 1) 
    lock = Lock()

    for i in range(0, nthreads):
        st = StressTester(i + 1, 0, 4, barrier, lock, 60)
        st.start()

    tmp = input("press any key to start")
    barrier.wait()


def test(request):
    transfers = TransferLogic.getFreuquentTransferTargeds(1)
    for transfer in transfers:
        print(transfer)
    print("n_transfers:", len(transfers))

def test2(request):
    pass

