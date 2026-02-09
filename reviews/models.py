"""
Модуль отзывов и рейтингов.
"""
from django.db import models
from django.conf import settings
from catalog.models import Product


class Review(models.Model):
    """Отзыв: ID, пользователь, товар, текст отзыва, рейтинг."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Товар'
    )
    text = models.TextField('Текст отзыва')
    rating = models.PositiveSmallIntegerField('Рейтинг', choices=[(i, str(i)) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = [['user', 'product']]

    def __str__(self):
        return f'{self.user} — {self.product} ({self.rating})'
