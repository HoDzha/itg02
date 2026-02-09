"""
Telegram-бот FlowerDelivery Master: получение заказов, уведомления о статусе, аналитика.
Запуск: python -m bot.run_bot (переменные берутся из .env или окружения)
"""
import asyncio
import os
import sys
import logging
from decimal import Decimal

# Загрузка .env до инициализации Django
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv(_root / '.env')

# Django setup для доступа к моделям и отправки уведомлений
sys.path.insert(0, str(_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')

import django
django.setup()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '🌸 FlowerDelivery Master\n\n'
        'Команды:\n'
        '/start — это сообщение\n'
        '/orders — последние заказы\n'
        '/stats — краткая аналитика по заказам\n\n'
        'Новые заказы с сайта приходят в этот чат автоматически.'
    )


def _fetch_orders_text() -> str:
    """Синхронный запрос к БД — выполняется в отдельном потоке."""
    from orders.models import Order
    orders = list(Order.objects.select_related('user').order_by('-created_at')[:10])
    if not orders:
        return 'Заказов пока нет.'
    lines = ['📦 Последние заказы:\n']
    for o in orders:
        name = (o.user.get_full_name() or o.user.username) if o.user_id else '—'
        lines.append(f'#{o.id} | {name} | {o.get_status_display()} | {o.created_at.strftime("%d.%m.%Y %H:%M")}')
    text = '\n'.join(lines)
    return text[:4000] + '…' if len(text) > 4096 else text


def _fetch_stats_text() -> str:
    """Синхронный запрос к БД — выполняется в отдельном потоке."""
    from orders.models import Order
    from django.db.models import Count
    from django.utils import timezone

    qs = Order.objects.exclude(status='cancelled')
    total_orders = qs.count()
    revenue = Decimal('0')
    for o in qs.prefetch_related('items'):
        revenue += o.total
    today = timezone.now().date()
    today_count = Order.objects.filter(created_at__date=today).exclude(status='cancelled').count()
    by_status = list(Order.objects.values('status').annotate(c=Count('id')))

    text = (
        '📊 Аналитика\n\n'
        f'Заказов сегодня: {today_count}\n'
        f'Всего заказов: {total_orders}\n'
        f'Выручка (всего): {revenue:.0f} ₽\n\n'
        'По статусам:\n' + '\n'.join(f"  {s['status']}: {s['c']}" for s in by_status)
    )
    return text[:4000] + '…' if len(text) > 4096 else text


async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _fetch_orders_text)
        await update.message.reply_text(text)
    except Exception as e:
        logger.exception('cmd_orders: %s', e)
        await update.message.reply_text(f'Ошибка: {e}')


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _fetch_stats_text)
        await update.message.reply_text(text)
    except Exception as e:
        logger.exception('cmd_stats: %s', e)
        await update.message.reply_text(f'Ошибка: {e}')


def main() -> None:
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error('Укажите TELEGRAM_BOT_TOKEN в окружении.')
        sys.exit(1)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('orders', cmd_orders))
    app.add_handler(CommandHandler('stats', cmd_stats))

    logger.info('Бот запущен.')
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
