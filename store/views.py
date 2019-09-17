from django.shortcuts import render
from .models import user, product
<<<<<<< Updated upstream
from django.views.decorators.http import require_http_methods
=======
from django.http import HttpResponse
>>>>>>> Stashed changes

# Create your views here.

@require_http_methods(["GET"])
def index(request):
    return render(request, "index.html", {"users": user.objects.all()})

@require_http_methods(["GET"])
def buy(request):
    return render(request, "buy.html", {
        "drinks": product.objects.filter(category="drink"),
        "candies": product.objects.filter(category="candy"),
    })

@require_http_methods(["GET"])
def charge(request):
    return render(request, "charge.html", {})


@require_http_methods(["GET"])
def transfer(request):
    return render(request, "transfer.html", {"users": user.objects.all()})

def test(request):
    response = "no"
    try:
       user.objects.get() 
       response = "yes"
    except user.DoesNotExist:
       pass
    return HttpResponse(response)
