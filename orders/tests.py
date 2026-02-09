from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from catalog.models import Product
from .models import Order
from .cart import get_cart, add_to_cart, CART_SESSION_KEY

User = get_user_model()


class CartTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name='Тюльпаны', price=800)

    def test_add_to_cart(self):
        class Req:
            session = None
        req = Req()
        req.session = self.client.session
        add_to_cart(req, self.product.id, 2)
        req.session.save()
        cart = get_cart(req)
        self.assertEqual(cart.get(str(self.product.id)), 2)

    def test_cart_view_anonymous(self):
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 200)


class CheckoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='pass123', email='b@b.com')
        self.product = Product.objects.create(name='Букет', price=1000)

    def test_checkout_requires_login(self):
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_order_creation(self):
        self.client.login(username='buyer', password='pass123')
        self.client.get(reverse('orders:cart_add', kwargs={'product_id': self.product.id}))
        response = self.client.post(reverse('orders:checkout'), {
            'delivery_address': 'ул. Тестовая, 1',
            'delivery_phone': '+79991234567',
            'comment': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)


class ReorderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reorderuser', password='pass123', email='r@r.com')
        self.product = Product.objects.create(name='Цветок', price=500)

    def test_reorder_adds_to_cart(self):
        order = Order.objects.create(user=self.user, delivery_address='A', delivery_phone='+7', status='delivered')
        order.items.create(product=self.product, quantity=3, price=self.product.price)
        self.client.login(username='reorderuser', password='pass123')
        response = self.client.get(reverse('orders:reorder', kwargs={'order_id': order.id}))
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get(CART_SESSION_KEY, {})
        self.assertEqual(cart.get(str(self.product.id)), 3)
