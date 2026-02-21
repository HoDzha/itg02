from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from catalog.models import Product
from .models import Order, OrderItem
from .cart import (
    get_cart_items, add_to_cart, remove_from_cart, set_cart_quantity,
    clear_cart, get_cart
)
from .forms import CheckoutForm
from .telegram_notify import send_order_to_telegram, send_status_to_telegram

# Ограничения количества в корзине
CART_QUANTITY_MIN = 1
CART_QUANTITY_MAX = 99


def _parse_quantity(value, default=1, allow_zero=False):
    """Безопасный парсинг количества: минимум 1 (или 0 при allow_zero), максимум CART_QUANTITY_MAX."""
    try:
        qty = int(value)
    except (TypeError, ValueError):
        return default
    if allow_zero and qty <= 0:
        return 0
    if qty < CART_QUANTITY_MIN:
        return CART_QUANTITY_MIN
    if qty > CART_QUANTITY_MAX:
        return CART_QUANTITY_MAX
    return qty


def _is_within_working_hours():
    """Проверка, что текущее время в рабочем интервале приёма заказов."""
    start = getattr(settings, 'ORDER_WORKING_HOURS_START', 9)
    end = getattr(settings, 'ORDER_WORKING_HOURS_END', 21)
    now = timezone.localtime(timezone.now())
    return start <= now.hour < end


def cart_view(request):
    items = get_cart_items(request)
    return render(request, 'orders/cart.html', {'cart_items': items})


def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    qty = _parse_quantity(request.GET.get('quantity', 1), default=1)
    add_to_cart(request, product_id, qty)
    messages.success(request, f'«{product.name}» добавлен в корзину.')
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'catalog:product_list'
    return redirect(next_url)


def cart_remove(request, product_id):
    remove_from_cart(request, product_id)
    messages.info(request, 'Позиция удалена из корзины.')
    return redirect('orders:cart')


def cart_update(request, product_id):
    if request.method != 'POST':
        return redirect('orders:cart')
    qty = _parse_quantity(request.POST.get('quantity', 0), default=0, allow_zero=True)
    set_cart_quantity(request, product_id, qty)
    return redirect('orders:cart')


@login_required
def checkout_view(request):
    items = get_cart_items(request)
    if not items:
        messages.warning(request, 'Корзина пуста.')
        return redirect('catalog:product_list')

    start_h = getattr(settings, 'ORDER_WORKING_HOURS_START', 9)
    end_h = getattr(settings, 'ORDER_WORKING_HOURS_END', 21)
    within_hours = _is_within_working_hours()
    if not within_hours:
        messages.info(
            request,
            f'Заказы принимаются только в рабочее время: с {start_h}:00 до {end_h}:00. '
            'Пожалуйста, оформите заказ в этот интервал или вернитесь позже.'
        )
        form = CheckoutForm(user=request.user)
        return render(request, 'orders/checkout.html', {'form': form, 'cart_items': items, 'within_working_hours': False})

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            if not _is_within_working_hours():
                messages.warning(
                    request,
                    f'К сожалению, рабочий день закончился (приём заказов с {start_h}:00 до {end_h}:00). '
                    'Пожалуйста, повторите попытку завтра.'
                )
                return render(request, 'orders/checkout.html', {'form': form, 'cart_items': items})
            order = Order.objects.create(
                user=request.user,
                delivery_address=form.cleaned_data['delivery_address'],
                delivery_phone=form.cleaned_data['delivery_phone'],
                comment=form.cleaned_data.get('comment', ''),
            )
            for product, qty in items:
                OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)
            clear_cart(request)
            send_order_to_telegram(order)
            messages.success(request, f'Заказ #{order.pk} оформлен.')
            return redirect('orders:order_detail', order_id=order.pk)
    else:
        form = CheckoutForm(user=request.user)

    return render(request, 'orders/checkout.html', {'form': form, 'cart_items': items, 'within_working_hours': True})


@login_required
def order_list_view(request):
    orders = request.user.orders.all()
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def reorder_view(request, order_id):
    """Повторный заказ: добавить все позиции из заказа в корзину."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    for item in order.items.select_related('product'):
        if item.product.is_available:
            add_to_cart(request, item.product_id, item.quantity)
    messages.success(request, 'Позиции из заказа добавлены в корзину.')
    return redirect('orders:cart')
