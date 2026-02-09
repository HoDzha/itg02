from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Order
from .telegram_notify import send_status_to_telegram


@receiver(pre_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            if old.status != instance.status:
                send_status_to_telegram(instance, old.status)
        except Order.DoesNotExist:
            pass
