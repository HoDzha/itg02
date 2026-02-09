from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from catalog.models import Product
from .models import Review
from .forms import ReviewForm


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if Review.objects.filter(user=request.user, product=product).exists():
        messages.warning(request, 'Вы уже оставили отзыв на этот товар.')
        return redirect('catalog:product_detail', pk=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.instance.product = product
            form.save()
            messages.success(request, 'Отзыв добавлен.')
            return redirect('catalog:product_detail', pk=product_id)
    else:
        form = ReviewForm()
    return render(request, 'reviews/review_form.html', {'form': form, 'product': product})
