from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from .models import User


class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser').exists())


class UserLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='loginuser', password='testpass123', email='u@u.com')
        self.client = Client()

    def test_login_page_loads(self):
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_authenticated(self):
        self.client.login(username='loginuser', password='testpass123')
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 302, 'Аутентифицированный пользователь должен перенаправляться с страницы входа')
        redirect_url = reverse(settings.LOGIN_REDIRECT_URL)
        self.assertTrue(
            response.url.endswith(redirect_url) or redirect_url in response.url,
            f'Редирект должен вести на {settings.LOGIN_REDIRECT_URL}, получен: {response.url}'
        )
