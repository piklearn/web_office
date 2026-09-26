from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Product, Category


class ProductListView(ListView):
    """لیست کالاها با امکان جستجو و فیلتر بر اساس دسته‌بندی."""
    model = Product
    template_name = "sales/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related("currency", "category")

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(short_description__icontains=q) | Q(sku__icontains=q)
            )

        category_slug = self.request.GET.get("category", "").strip()
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["current_category"] = self.request.GET.get("category", "")
        context["query"] = self.request.GET.get("q", "")
        return context


class ProductDetailView(DetailView):
    """جزئیات یک کالا شامل ویژگی‌ها و توضیحات کامل."""
    model = Product
    template_name = "sales/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related("currency", "category").prefetch_related("features")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context["related_products"] = (
            Product.objects.filter(is_active=True, category=product.category)
            .exclude(pk=product.pk)[:4]
            if product.category else Product.objects.none()
        )
        return context
