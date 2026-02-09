from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from catalog.models import Product
from .models import Review

User = get_user_model()


class ReviewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reviewer', password='pass123', email='r@r.com')
        self.product = Product.objects.create(name='Букет', price=1000)

    def test_add_review_requires_login(self):
        response = self.client.get(reverse('reviews:add_review', kwargs={'product_id': self.product.id}))
        self.assertEqual(response.status_code, 302)

    def test_add_review_creates_review(self):
        self.client.login(username='reviewer', password='pass123')
        response = self.client.post(
            reverse('reviews:add_review', kwargs={'product_id': self.product.id}),
            {'text': 'Отличный букет!', 'rating': 5}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(user=self.user, product=self.product).exists())
        self.assertEqual(Review.objects.get(user=self.user, product=self.product).rating, 5)
