from django.shortcuts import render, reverse
from .models import User, Product, UserIdentifierTypes, ProductIdentifierTypes
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import logout as auth_logout
from .backend import *
from .store_exceptions import *
from .stresstest import *


@require_http_methods(["GET"])
def index(request):
    """
    GET: Return the rendered index page. Users can login here.
    """
    return render(request, "index.html", {
        "users": UserLogic.getFrequentUsersList(),
        "ident_types": UserIdentifierTypes.to_dict(),
    })


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def buy(request):
    """
    GET: Return the rendered page to buy products
    POST: Puchase a product
        @body_param product_id: int
        @body_param token: int
    """
    if request.method == 'GET':  # Return the rendered page
        return render(request, "buy.html", {
            "most_bought": ProductLogic.getMostBoughtProductsList(),
            "recently_bought": ProductLogic.getLastBoughtProductsList(request.user.id),
            "drinks": ProductLogic.getDrinks(),
            "candies": ProductLogic.getCandies(),
            "products": Product.objects.all(),
            "ident_types": ProductIdentifierTypes.to_dict(),
        })
    elif request.method == 'POST':  # Perform a purchase
        user_id = request.user.id
        identifier = request.POST.get("identifier")
        identifier_type = request.POST.get("identifier_type")
        token = request.POST.get("token")
        try:
            purchase_return_tuple = PurchaseLogic.purchase(user_id, identifier, identifier_type, token)
        except (UserNotEnoughMoney, NegativeMoneyAmount) as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        if purchase_return_tuple >= 0:
            return JsonResponse({"purchase_id": purchase_return_tuple})
        else:
            return HttpResponse(status=400)


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def buy_revert(request):
    """
    POST: Revert a purchase.
        @body_param token: int
        @body_param purchase_id: int
    """
    purchase_id = request.POST.get("purchase_id")
    token = request.POST.get("token")
    try:
        PurchaseLogic.annullatePurchase(purchase_id, token)
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
        @body_param token: int
        @body_param amount: float
    """
    if request.method == "GET":
        return render(request, "charge.html", {
            "recent_charges": ChargeLogic.getLastChargesList(request.user.id),
        })
    elif request.method == "POST":
        user_id = request.user.id
        token = request.POST.get("token")
        amount = request.POST.get("amount")
        amount = Decimal(amount)
        try:
            charge_id = ChargeLogic.charge(user_id, amount, token)
        except NegativeMoneyAmount as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        return JsonResponse({'charge_id': charge_id})


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def charge_revert(request):
    """
    POST: Revert a charge.
        @body_param charge_id: int
        @body_param token: int
    """
    charge_id = request.POST.get("charge_id")
    token = request.POST.get("token")
    try:
        ChargeLogic.annullateCharge(charge_id, token)
    except (ChargeNotAnnullable, UserNotEnoughMoney) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url="index")
@require_http_methods(["GET", "POST"])
@csrf_protect
def transfer(request):
    """
    GET: Return the rendered page to transfer money to another user.
    POST: Transfer money to another user.
        @body_param token: int
        @body_param receiver: int
        @body_param amount: float
    """
    if request.method == "GET":
        return render(request, "transfer.html", {
            "users": TransferLogic.getFreuquentTransferTargeds(request.user.id),
            "recent_transfers": TransferLogic.getLastTransfers(request.user.id),
        })
    elif request.method == "POST":
        user_id = request.user.id
        token = request.POST.get("token")
        receiver_id = request.POST.get("receiver")
        amount = Decimal(request.POST.get("amount"))
        try:
            transfer_id = TransferLogic.transfer(
                user_id, receiver_id, amount, token)
        except (UserNotEnoughMoney, NegativeMoneyAmount) as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        return JsonResponse({"transfer_id": transfer_id})


@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def transfer_revert(request):
    """
    POST: Revert a transfer.
        @body_param transfer_id: int
        @body_param token: int
    """
    transfer_id = request.POST.get('transfer_id')
    token = request.POST.get('token')
    try:
        TransferLogic.annullateTransfer(transfer_id, token)
    except (TransferNotAnnullable, UserNotEnoughMoney) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return HttpResponse(status=200)


# Authentication

@require_http_methods(["POST"])
@csrf_protect
def login(request):
    """
    Login an user.
    @body_param identifier: string/int
    @body_param identifier_type: int
    """
    identifier = request.POST.get('identifier')
    ident_type = request.POST.get('identifier_type')
    try:
        UserLogic.login(request, identifier, ident_type)
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


# At-most-once token

@login_required(login_url="index")
@require_http_methods(["POST"])
@csrf_protect
def getToken(request):
    """
    Return a new token used for the at-most-once protocol.
    """
    token = TokenLogic.get_token()
    return JsonResponse({"token": token})


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
