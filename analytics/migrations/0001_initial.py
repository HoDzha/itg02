# Generated manually for FlowerDelivery Master

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата')),
                ('sales_data', models.JSONField(blank=True, default=dict, verbose_name='Данные по продажам')),
                ('profit', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Прибыль')),
                ('expenses', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Расходы')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Создал')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to='orders.order', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Отчёт',
                'verbose_name_plural': 'Отчёты',
                'ordering': ['-date'],
            },
        ),
    ]
