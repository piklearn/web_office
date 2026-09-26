from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    # از str به‌جای slug استفاده شده چون اسلاگ‌های فارسی (unicode) با کانورتر slug سازگار نیستند
    path("<str:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
]
