"""
Отправка заказов и уведомлений о статусе в Telegram.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _send_telegram(text: str, chat_id: str = None) -> bool:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    chat_id = chat_id or getattr(settings, 'TELEGRAM_ORDER_CHAT_ID', None)
    if not token or not chat_id:
        return False
    try:
        import requests
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        r = requests.post(url, json={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.exception('Telegram send error: %s', e)
        return False


def send_order_to_telegram(order) -> bool:
    lines = [
        f'🆕 <b>Новый заказ #{order.pk}</b>',
        f'Клиент: {order.user.get_full_name() or order.user.username}',
        f'Email: {order.user.email}',
        f'Телефон: {order.delivery_phone}',
        f'Адрес: {order.delivery_address}',
        '',
        'Позиции:',
    ]
    for item in order.items.select_related('product'):
        lines.append(f'  • {item.product.name} x {item.quantity} = {item.subtotal} ₽')
    lines.append(f'\n<b>Итого: {order.total} ₽</b>')
    if order.comment:
        lines.append(f'\nКомментарий: {order.comment}')
    return _send_telegram('\n'.join(lines))


def send_status_to_telegram(order, old_status: str = None) -> bool:
    text = f'📦 Статус заказа #{order.pk} изменён: {order.get_status_display()}'
    return _send_telegram(text)
