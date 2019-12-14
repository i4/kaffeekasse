# SPDX-License-Identifier: GPL-3.0-or-later

from decimal import Decimal, InvalidOperation

import django.contrib.auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

import store.backend as backend
import store.config as config
import store.models as models
from store.exceptions import ClientMessageException


def permit_direct_login(request):
    # User certificates not enforced, permit all clients
    if config.RESTRICT_CLIENT_CERTS is None:
        return True

    if request.headers['cert-verify'] != 'SUCCESS':
        return False
    if request.headers['cert-cn'] not in config.RESTRICT_CLIENT_CERTS:
        return False

    return True


@require_http_methods(['GET'])
def index(request):
    """
    GET: Return the rendered index page. Users can login here.
    """

    if not permit_direct_login(request):
        return redirect_to_login(reverse('buy'), login_url='password_login')

    django.contrib.auth.logout(request)
    return render(request, 'index.html', {
        'direct_login': permit_direct_login(request),
        'users': backend.UserLogic.getFrequentUsersList(),
        'ident_types': models.UserIdentifier,
    })


@login_required(login_url='index')
@require_http_methods(['GET', 'POST'])
@csrf_protect
def buy(request):
    """
    GET: Return the rendered page to buy products
    POST: Puchase a product and return the product id and the purchase id as JsonResponse
    """

    user_id = request.user.userdata.id

    if request.method == 'GET':  # Return the rendered page
        return render(request, 'buy.html', {
            'direct_login': permit_direct_login(request),
            'most_bought': backend.ProductLogic.getMostBoughtProductsList(user_id),
            'recently_bought': backend.ProductLogic.getLastBoughtProductsList(user_id),
            'categories': [{
                'name': 'Getränke',
                'id': 'drinks',
                'products': backend.ProductLogic.getDrinks(),
            }, {
                'name': 'Nahrung',
                'id': 'candies',
                'products': backend.ProductLogic.getCandies(),
            }],
            'products': models.Product.objects.all(),
            'ident_types': models.ProductIdentifier,
            'config': config,
        })

    if request.method == 'POST':  # Perform a purchase
        ident = request.POST.get('ident')
        ident_type = int(request.POST.get('ident_type'))

        try:
            purchase_return_tuple = backend.PurchaseLogic.purchase(user_id, ident, ident_type)
        except ClientMessageException as e:
            return JsonResponse({'error': str(e)}, status=400)

        if purchase_return_tuple[0] >= 0:
            return JsonResponse({
                'purchase_id': purchase_return_tuple[0],
                'product_id': purchase_return_tuple[1],
            })

        # TODO: Also return product id
        return HttpResponse(status=400)

    assert False


@login_required(login_url='index')
@require_http_methods(['POST'])
@csrf_protect
def buy_revert(request):
    """
    POST: Revert a purchase.
    """

    purchase_id = int(request.POST.get('purchase_id'))

    try:
        backend.PurchaseLogic.annulPurchase(purchase_id)
    except ClientMessageException as e:
        return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url='index')
@require_http_methods(['GET', 'POST'])
@csrf_protect
def charge(request):
    """
    GET: Show the rendered page to charge money.
    POST: Charge money.
    """

    if not config.CHARGE_PERMIT_MANUAL:
        return HttpResponse(status=400)

    user_id = request.user.userdata.id

    if request.method == 'GET':
        return render(request, 'charge.html', {
            'direct_login': permit_direct_login(request),
            'recent_charges': backend.ChargeLogic.getLastChargesList(user_id),
            'config': config,
        })

    if request.method == 'POST':
        amount = request.POST.get('amount')
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


@login_required(login_url='index')
@require_http_methods(['POST'])
@csrf_protect
def charge_revert(request):
    """
    POST: Revert a charge.
    """
    charge_id = int(request.POST.get('charge_id'))
    try:
        backend.ChargeLogic.annulCharge(charge_id)
    except ClientMessageException as e:
        return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=200)


@login_required(login_url='index')
@require_http_methods(['GET', 'POST'])
@csrf_protect
def transfer(request):
    """
    GET: Return the rendered page to transfer money to another user.
    POST: Transfer money to another user.
    """

    user_id = request.user.userdata.id

    if request.method == 'GET':
        return render(request, 'transfer.html', {
            'direct_login': permit_direct_login(request),
            'users': backend.TransferLogic.getFrequentTransferTargets(user_id),
            'recent_transfers': backend.TransferLogic.getLastTransfers(user_id),
            'ident_types': models.UserIdentifier,
            'config': config,
        })

    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_ident')
        receiver_ident_type = int(request.POST.get('ident_type'))
        try:
            amount = Decimal(request.POST.get('amount'))
        except InvalidOperation as e:
            return JsonResponse({'error': str(e)}, status=400)
        try:
            transfer_tuple = backend.TransferLogic.transfer(
                user_id, receiver_id, receiver_ident_type, amount)
        except ClientMessageException as e:
            return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse({'transfer_id': transfer_tuple[0], 'receiver_id': transfer_tuple[1]})

    assert False


@login_required(login_url='index')
@require_http_methods(['POST'])
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

@require_http_methods(['POST'])
@csrf_protect
def login(request):
    """
    Login an user.
    """

    if not permit_direct_login(request):
        return HttpResponse(status=403)

    ident = request.POST.get('ident')
    ident_type = int(request.POST.get('ident_type'))
    try:
        backend.UserLogic.login(request, ident, ident_type)
    # TODO: Show errors on login page
    except ClientMessageException as e:
        print(ident, ident_type, e)
        return HttpResponseRedirect(reverse('index'))

    return HttpResponseRedirect(reverse('buy'))


@login_required(login_url='index')
@csrf_protect
def logout(request):
    """
    Logout the current user.
    """
    django.contrib.auth.logout(request)
    return HttpResponseRedirect(reverse('index'))
