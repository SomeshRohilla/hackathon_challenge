from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import SalesData, Product
from .forecast import generate_forecast
from .serializers import ProductSerializer


# ---------------- BASIC VIEWS ----------------

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


def home(request):
    return render(request, "home.html")


def stockedit(request):
    context = {}
    product = Product.objects.all()
    context['product']=product
    return render(request,'stockedit.html' , context)




def aipredict(request):
    return render(request, "aipredict.html")


# ---------------- FORECAST API (MAIN) ----------------

@api_view(['GET'])
def forecast_api(request):

    

    # 🔥 FORECAST
    forecast_data = generate_forecast(days=365)
    full_forecast = forecast_data["forecast"]

    forecast_7_days = full_forecast[:7]
    forecast_30_days = full_forecast[:30]
    forecast_365_days = full_forecast

    if not forecast_data or "forecast" not in forecast_data:
        return Response({"error": "Not enough data for forecast"}, status=400)

    # 🔥 STOCK PER PRODUCT + SIZE (FIXED)
    products = Product.objects.all()
    stock_summary = []

    for product in products:

        sizes = ['Small', 'Medium', 'Large']
        size_stock = {}

        for size in sizes:
            latest = (
                SalesData.objects
                .filter(product=product, size=size)
                .order_by('-date')
                .first()
            )

            size_stock[size] = latest.stock_level if latest else 0

        stock_summary.append({
            "product_id": product.product_id,
            "sizes": size_stock
        })

    # 🔥 SAFE CHECK
    if not forecast_data["forecast"]:
        return Response({"error": "No forecast generated"}, status=400)

    # 🔥 TODAY SUMMARY
    first_day = full_forecast[0]

    sizes = ['Small', 'Medium', 'Large']

    today_sizes = {}

    for size in sizes:
        if size in first_day["mugs"]:
            today_sizes[size] = first_day["mugs"][size]
        else:
            today_sizes[size] = {
                "predicted_sales": 0,
                "min_sales": 0,
                "max_sales": 0,
                "remaining_stock": 0
            }

    today_summary = {
        "date": first_day["date"],
        "sizes": today_sizes
    }
    return Response({
        "product": "ALL PRODUCTS",
        "products_stock": stock_summary,
        "today": today_summary,
        "forecast_7_days": forecast_7_days,
        "forecast_30_days": forecast_30_days,
        "forecast_365_days": forecast_365_days
})
# ---------------- PRODUCT CRUD ----------------

@api_view(['GET', 'POST'])
def product_list_create(request):

    if request.method == 'GET':
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors)


@api_view(['PUT', 'DELETE'])
def product_update_delete(request, pk):

    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Not found"})

    if request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors)

    elif request.method == 'DELETE':
        product.delete()
        return Response({"message": "Deleted"})


# ---------------- DAILY SALES API ----------------

@api_view(['GET'])
def daily_sales_api(request):

    data = (
        SalesData.objects
        .values('date')
        .annotate(total_sales=Sum('daily_sales'))
        .order_by('date')
    )

    return Response(list(data))