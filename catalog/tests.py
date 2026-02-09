from django.test import TestCase, Client
from django.urls import reverse
from .models import Product


class CatalogTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name='Розы', price=1500, description='Букет роз')

    def test_product_list_loads(self):
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Розы')

    def test_product_detail_loads(self):
        response = self.client.get(reverse('catalog:product_detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Розы')
        self.assertContains(response, '1500')
