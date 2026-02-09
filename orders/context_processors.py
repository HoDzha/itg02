"""
Контекст-процессор: итог и количество позиций в корзине для шаблонов.
"""
from .cart import get_cart_total, get_cart_items


def cart_total(request):
    items = get_cart_items(request)
    total = get_cart_total(request)
    count = sum(qty for _, qty in items)
    return {'cart_total': total, 'cart_count': count}
