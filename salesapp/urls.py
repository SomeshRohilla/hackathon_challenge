from django.urls import path
from . import views

urlpatterns = [
    # 🔐 Auth
    path('', views.login_view, name="login"),
    path('home/', views.home, name="home"),

    # 📦 UI Pages
    path('stockedit/', views.stockedit, name="stockedit"),
    path('aipredict/', views.aipredict, name="aipredict"),

    # 🤖 Forecast API
    path('forecast/', views.forecast_api, name="forecast"),

    # 📦 Product APIs
    path('products/', views.product_list_create, name="products"),
    path('products/<int:pk>/', views.product_update_delete, name="product-detail"),

    # 📊 Sales API
    path('daily-sales/', views.daily_sales_api, name="daily-sales"),
]