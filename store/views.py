from decimal import Decimal, InvalidOperation

import django.contrib.auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

import store.backend as backend
import store.models as models
from store.store_config import KAFFEEKASSE as config
from store.store_exceptions import ClientMessageException


@require_http_methods(["GET"])
def index(request):
    """
    GET: Return the rendered index page. Users can login here.
    """
    django.contrib.auth.logout(request)
    return render(request, "index.html", {
        "users": backend.UserLogic.getFrequentUsersList(),
        "ident_types": models.UserIdentifier,
    })


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def buy(request):
    """
    GET: Return the rendered page to buy products
    POST: Puchase a product and return the product id and the purchase id as JsonResponse
    """

    user_id = request.user.id

    if request.method == 'GET':  # Return the rendered page
        return render(request, "buy.html", {
            "most_bought": backend.ProductLogic.getMostBoughtProductsList(),
            "recently_bought": backend.ProductLogic.getLastBoughtProductsList(user_id),
            "drinks": backend.ProductLogic.getDrinks(),
            "candies": backend.ProductLogic.getCandies(),
            "products": models.Product.objects.all(),
            "ident_types": models.ProductIdentifier,
            "config": config,
        })

    if request.method == 'POST':  # Perform a purchase
        ident = request.POST.get("ident")
        ident_type = int(request.POST.get("ident_type"))

        try:
            purchase_return_tuple = backend.PurchaseLogic.purchase(user_id, ident, ident_type)
        except ClientMessageException as e:
            return JsonResponse({'error': str(e)}, status=400)

        if purchase_return_tuple[0] >= 0:
            return JsonResponse({
                "purchase_id": purchase_return_tuple[0],
                "product_id": purchase_return_tuple[1],
            })

        # TODO: Also return product id
        return HttpResponse(status=400)

    assert False


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def buy_revert(request):
    """
    POST: Revert a purchase.
    """

    purchase_id = int(request.POST.get("purchase_id"))

    try:
        backend.PurchaseLogic.annulPurchase(purchase_id)
    except ClientMessageException as e:
        return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def charge(request):
    """
    GET: Show the rendered page to charge money.
    POST: Charge money.
    """

    user_id = request.user.id

    if request.method == "GET":
        return render(request, "charge.html", {
            "recent_charges": backend.ChargeLogic.getLastChargesList(user_id),
            "config": config,
        })

    if request.method == "POST":
        amount = request.POST.get("amount")
        try:
            amount = Decimal(amount)
        except InvalidOperation as e:
            return JsonResponse({'error': str(e)}, status=400)
        try:
            charge_id = backend.ChargeLogic.charge(user_id, amount)
        except ClientMessageException as e:
            return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse({'charge_id': charge_id})

    assert False


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def charge_revert(request):
    """
    POST: Revert a charge.
    """
    charge_id = int(request.POST.get("charge_id"))
    try:
        backend.ChargeLogic.annulCharge(charge_id)
    except ClientMessageException as e:
        return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def transfer(request):
    """
    GET: Return the rendered page to transfer money to another user.
    POST: Transfer money to another user.
    """

    user_id = request.user.id

    if request.method == "GET":
        return render(request, "transfer.html", {
            "users": backend.TransferLogic.getFrequentTransferTargets(user_id),
            "recent_transfers": backend.TransferLogic.getLastTransfers(user_id),
            "ident_types": models.UserIdentifier,
            "config": config,
        })

    if request.method == "POST":
        receiver_id = request.POST.get("receiver_ident")
        receiver_ident_type = int(request.POST.get("ident_type"))
        try:
            amount = Decimal(request.POST.get("amount"))
        except InvalidOperation as e:
            return JsonResponse({'error': str(e)}, status=400)
        try:
            transfer_tuple = backend.TransferLogic.transfer(
                user_id, receiver_id, receiver_ident_type, amount)
        except ClientMessageException as e:
            return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse({"transfer_id": transfer_tuple[0], "receiver_id": transfer_tuple[1]})

    assert False


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def transfer_revert(request):
    """
    POST: Revert a transfer.
    """
    transfer_id = int(request.POST.get('transfer_id'))
    try:
        backend.TransferLogic.annulTransfer(transfer_id)
    except ClientMessageException as e:
        return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=200)


# Authentication

@require_http_methods(["POST"])
@csrf_protect
def login(request):
    """
    Login an user.
    """
    ident = request.POST.get('ident')
    ident_type = int(request.POST.get('ident_type'))
    try:
        backend.UserLogic.login(request, ident, ident_type)
    # TODO: Show errors on login page
    except ClientMessageException as e:
        print(ident, ident_type, e)
        return HttpResponseRedirect(reverse("index"))

    return HttpResponseRedirect(reverse("buy"))


@login_required(login_url="index")
@csrf_protect
def logout(request):
    """
    Logout the current user.
    """
    django.contrib.auth.logout(request)
    return HttpResponseRedirect(reverse("index"))
