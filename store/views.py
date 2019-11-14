from django.shortcuts import render, reverse
from .models import User, Product
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import logout as auth_logout
from .backend import *
from .store_exceptions import *
from .store_config import KAFFEEKASSE as config
from decimal import InvalidOperation


@require_http_methods(["GET"])
def index(request):
    """
    GET: Return the rendered index page. Users can login here.
    """
    auth_logout(request)
    return render(request, "index.html", {
        "users": UserLogic.getFrequentUsersList(),
        "ident_types": UserIdentifier,
    })


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def buy(request):
    """
    GET: Return the rendered page to buy products
    POST: Puchase a product and return the product id and the purchase id as JsonResponse
        :body_param ident:  The identifier of the product
        :body_param ident_type: int The identifier type of the product
    """

    if request.method == 'GET':  # Return the rendered page
        return render(request, "buy.html", {
            "most_bought": ProductLogic.getMostBoughtProductsList(),
            "recently_bought": ProductLogic.getLastBoughtProductsList(request.user.id),
            "drinks": ProductLogic.getDrinks(),
            "candies": ProductLogic.getCandies(),
            "products": Product.objects.all(),
            "ident_types": ProductIdentifier,
            "config": config,
        })

    elif request.method == 'POST':  # Perform a purchase
        user_id = request.user.id
        ident = request.POST.get("ident")
        ident_type = int(request.POST.get("ident_type"))

        try:
            purchase_return_tuple = PurchaseLogic.purchase(user_id, ident, ident_type)
        except (UserNotEnoughMoney, NegativeMoneyAmount, UserIdentifierNotExists) as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        if purchase_return_tuple[0] >= 0:
            return JsonResponse({
                "purchase_id": purchase_return_tuple[0],
                "product_id": purchase_return_tuple[1],
            })
            # TODO: Also return product id
        else:
            return HttpResponse(status=400)


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def buy_revert(request):
    """
    POST: Revert a purchase.
        :body_param purchase_id: int
    """

    purchase_id = int(request.POST.get("purchase_id"))

    try:
        PurchaseLogic.annullatePurchase(purchase_id)
    except (PurchaseNotAnnullable, UserNotEnoughMoney) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def charge(request):
    """
    GET: Show the rendered page to charge money.
    POST: Charge money.
        :body_param amount: float
    """
    if request.method == "GET":
        return render(request, "charge.html", {
            "recent_charges": ChargeLogic.getLastChargesList(request.user.id),
            "config": config,
        })
    elif request.method == "POST":
        user_id = request.user.id
        amount = request.POST.get("amount")
        try:
            amount = Decimal(amount)
        except InvalidOperation as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        try:
            charge_id = ChargeLogic.charge(user_id, amount)
        except NegativeMoneyAmount as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        return JsonResponse({'charge_id': charge_id})


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def charge_revert(request):
    """
    POST: Revert a charge.
        :body_param charge_id: int
    """
    charge_id = int(request.POST.get("charge_id"))
    try:
        ChargeLogic.annullateCharge(charge_id)
    except (ChargeNotAnnullable, UserNotEnoughMoney, NegativeMoneyAmount) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def transfer(request):
    """
    GET: Return the rendered page to transfer money to another user.
    POST: Transfer money to another user.
        :body_param receiver: int
        :body_param amount: float
    """
    if request.method == "GET":
        return render(request, "transfer.html", {
            "users": TransferLogic.getFreuquentTransferTargets(request.user.id),
            "recent_transfers": TransferLogic.getLastTransfers(request.user.id),
            "ident_types": UserIdentifier,
            "config": config,
        })
    elif request.method == "POST":
        user_id = request.user.id
        receiver_id = request.POST.get("receiver_ident")
        receiver_ident_type = int(request.POST.get("ident_type"))
        try:
            amount = Decimal(request.POST.get("amount"))
        except InvalidOperation as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        try:
            transfer_tuple = TransferLogic.transfer(
                user_id, receiver_id, receiver_ident_type, amount)
        except (UserNotEnoughMoney, NegativeMoneyAmount, UserIdentifierNotExists, SenderEqualsReceiverError) as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        return JsonResponse({"transfer_id": transfer_tuple[0], "receiver_id": transfer_tuple[1]})


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def transfer_revert(request):
    """
    POST: Revert a transfer.
        :body_param transfer_id: int
    """
    transfer_id = int(request.POST.get('transfer_id'))
    try:
        TransferLogic.annullateTransfer(transfer_id)
    except (TransferNotAnnullable, UserNotEnoughMoney, NegativeMoneyAmount) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


# Authentication

@require_http_methods(["POST"])
@csrf_protect
def login(request):
    """
    Login an user.
    :body_param ident: string/int
    :body_param ident_type: int
    """
    ident = request.POST.get('ident')
    ident_type = int(request.POST.get('ident_type'))
    try:
        UserLogic.login(request, ident, ident_type)
    except (UserIdentifierNotExists, DisabledIdentifier):
        return HttpResponseRedirect(reverse("index"))

    return HttpResponseRedirect(reverse("buy"))


@login_required(login_url="index")
@csrf_protect
def logout(request):
    """
    Logout the current user.
    """
    auth_logout(request)
    return HttpResponseRedirect(reverse("index"))
