"""
Корзина на основе сессии: {product_id: quantity}.
"""
from decimal import Decimal
from catalog.models import Product


CART_SESSION_KEY = 'cart'


def get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})


def set_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def add_to_cart(request, product_id, quantity=1):
    cart = get_cart(request)
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + quantity
    set_cart(request, cart)


def remove_from_cart(request, product_id):
    cart = get_cart(request)
    cart.pop(str(product_id), None)
    set_cart(request, cart)


def set_cart_quantity(request, product_id, quantity):
    if quantity <= 0:
        remove_from_cart(request, product_id)
        return
    cart = get_cart(request)
    cart[str(product_id)] = quantity
    set_cart(request, cart)


def clear_cart(request):
    set_cart(request, {})


def get_cart_items(request):
    """Список (Product, quantity) для отображения корзины."""
    cart = get_cart(request)
    if not cart:
        return []
    products = Product.objects.filter(id__in=cart.keys(), is_available=True)
    return [(p, cart[str(p.id)]) for p in products]


def get_cart_total(request):
    """Сумма корзины."""
    items = get_cart_items(request)
    return sum(Decimal(str(p.price)) * qty for p, qty in items)
