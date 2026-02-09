from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Product
from reviews.models import Review


class ProductListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'catalog/product_list.html'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(is_available=True)


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    reviews = product.reviews.select_related('user').order_by('-created_at')[:10]
    return render(request, 'catalog/product_detail.html', {'product': product, 'reviews': reviews})
