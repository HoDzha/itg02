"""
Модуль аналитики и отчётов.
"""
from django.db import models
from django.conf import settings


class Report(models.Model):
    """Отчёт: ID, дата, заказ (опционально), данные по продажам, прибыль, расходы."""
    date = models.DateField('Дата')
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name='Заказ'
    )
    sales_data = models.JSONField('Данные по продажам', default=dict, blank=True)
    profit = models.DecimalField('Прибыль', max_digits=12, decimal_places=2, default=0)
    expenses = models.DecimalField('Расходы', max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал'
    )

    class Meta:
        verbose_name = 'Отчёт'
        verbose_name_plural = 'Отчёты'
        ordering = ['-date']

    def __str__(self):
        return f'Отчёт за {self.date}'
