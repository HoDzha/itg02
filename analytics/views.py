from decimal import Decimal
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.utils import timezone
from orders.models import Order


@staff_member_required
def analytics_dashboard(request):
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today).exclude(status='cancelled')
    total_orders = Order.objects.exclude(status='cancelled').count()
    revenue = Decimal('0')
    for o in Order.objects.exclude(status='cancelled').prefetch_related('items'):
        revenue += o.total
    orders_by_status = Order.objects.values('status').annotate(c=Count('id')).order_by('-c')
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:20]
    return render(request, 'analytics/dashboard.html', {
        'orders_today': orders_today.count(),
        'total_orders': total_orders,
        'revenue': revenue,
        'orders_by_status': orders_by_status,
        'recent_orders': recent_orders,
    })


@staff_member_required
def analytics_reports(request):
    from .models import Report
    reports = Report.objects.select_related('order').order_by('-date')[:50]
    return render(request, 'analytics/reports.html', {'reports': reports})
