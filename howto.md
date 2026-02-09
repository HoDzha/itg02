# FlowerDelivery Master — как всё устроено

Документ описывает алгоритм работы проекта, общую структуру и назначение каждого файла.

---

## 1. Алгоритм работы системы

### 1.1 Общий поток

1. **Пользователь заходит на сайт** → Django обрабатывает запрос по `ROOT_URLCONF` (`flower_delivery.urls`).
2. **Маршрутизация** → URL разбирается по приложениям: каталог (главная), пользователи, заказы, отзывы, аналитика.
3. **Шаблоны** → Каждая страница наследует `templates/base.html` (навигация, корзина в шапке, сообщения, подвал).
4. **Корзина** → Хранится в сессии как словарь `{product_id: quantity}`. Контекст-процессор добавляет в каждый запрос `cart_total` (сумма) и `cart_count` (количество позиций).
5. **Оформление заказа** → Только для авторизованных. Создаётся `Order` и `OrderItem`, корзина очищается, текст заказа отправляется в Telegram (если заданы токен и chat_id).
6. **Смена статуса заказа** → В админке администратор меняет статус → срабатывает сигнал `pre_save` → в Telegram уходит уведомление о новом статусе.
7. **Telegram-бот** → Отдельный процесс. По командам `/orders` и `/stats` читает данные из той же БД (через Django ORM после `django.setup()`).

### 1.2 Поток данных: от каталога до заказа

```
Каталог (Product) → «В корзину» → сессия['cart'][product_id] = quantity
→ Страница «Корзина» (чтение сессии + Product по id)
→ «Оформить заказ» (только если пользователь залогинен)
→ Форма: адрес, телефон, комментарий
→ POST → создаётся Order + OrderItem по текущей корзине
→ Корзина очищается → редирект на «Мой заказ»
→ send_order_to_telegram(order) → запрос к API Telegram
```

### 1.3 Интеграция с Telegram

- **Сайт → Telegram:** при создании заказа вызывается `orders.telegram_notify.send_order_to_telegram(order)`; при сохранении заказа в админке с изменённым статусом сигнал `orders.signals.order_status_changed` вызывает `send_status_to_telegram(order)`.
- **Бот:** запускается как отдельный процесс (`python -m bot.run_bot`), поднимает Django через `django.setup()`, обрабатывает команды и читает/агрегирует заказы из БД. В один чат можно и слать уведомления с сайта (по `TELEGRAM_ORDER_CHAT_ID`), и общаться с ботом (команды).

---

## 2. Общая структура проекта

```
itogpythoncursor/
├── manage.py                 # Точка входа Django (миграции, runserver, test)
├── requirements.txt          # Зависимости Python
├── .env.example              # Пример переменных окружения
├── .env                      # Реальные переменные (не в git), загружаются через python-dotenv
│
├── flower_delivery/          # Настройки проекта Django
│   ├── __init__.py
│   ├── settings.py          # Конфигурация, загрузка .env, AUTH_USER_MODEL, Telegram
│   ├── urls.py               # Корневой маршрутизатор URL
│   └── wsgi.py               # WSGI-приложение для деплоя
│
├── users/                    # Регистрация, авторизация, профиль
├── catalog/                  # Каталог товаров (цветы)
├── orders/                   # Корзина, оформление заказа, история, повторный заказ, Telegram-уведомления
├── reviews/                  # Отзывы и рейтинг по товарам
├── analytics/                # Дашборд и отчёты для staff
│
├── bot/                      # Telegram-бот (отдельный процесс)
│   ├── __init__.py
│   └── run_bot.py            # Запуск бота, команды /start, /orders, /stats
│
├── templates/                # Общие шаблоны (DIRS в settings)
│   ├── base.html             # Базовый layout (навбар, корзина, сообщения, footer)
│   ├── catalog/
│   ├── users/
│   ├── orders/
│   ├── reviews/
│   └── analytics/
│
├── static/                   # Статика (Bootstrap подключается из CDN в base.html)
└── media/                    # Загруженные файлы (изображения товаров), создаётся при работе
```

---

## 3. Описание файлов по модулям

### 3.1 Корень проекта

| Файл | Назначение |
|------|------------|
| **manage.py** | Стандартная точка входа Django. Устанавливает `DJANGO_SETTINGS_MODULE=flower_delivery.settings` и вызывает `execute_from_command_line(sys.argv)` — миграции, `runserver`, `createsuperuser`, `test` и т.д. |
| **requirements.txt** | Зависимости: Django, python-dotenv, Pillow (изображения), python-telegram-bot, requests (Telegram API), django-crispy-forms и crispy-bootstrap5 для форм. |
| **.env.example** | Пример переменных: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ORDER_CHAT_ID`, `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`. Копируется в `.env` и заполняется. |

---

### 3.2 flower_delivery/ (ядро Django)

| Файл | Назначение |
|------|------------|
| **settings.py** | Загружает `.env` через `load_dotenv(BASE_DIR / '.env')`. Задаёт приложения (users, catalog, orders, reviews, analytics, crispy), middleware, шаблоны с контекст-процессором `orders.context_processors.cart_total`. База — SQLite, медиа/статика, `AUTH_USER_MODEL = 'users.User'`, редиректы логина/логаута, `LOGIN_URL`. Отдельно выносит `TELEGRAM_BOT_TOKEN` и `TELEGRAM_ORDER_CHAT_ID` из окружения. |
| **urls.py** | Подключает: `admin/`, каталог (корень `''`), `users/`, `orders/`, `reviews/`, `analytics/`. В DEBUG добавляет раздачу медиа из `MEDIA_ROOT`. |
| **wsgi.py** | Устанавливает `DJANGO_SETTINGS_MODULE` и возвращает `get_wsgi_application()` — используется веб-сервером (gunicorn/uWSGI и т.п.). |

---

### 3.3 users/ — пользователи

| Файл | Назначение |
|------|------------|
| **models.py** | Модель `User(AbstractUser)` с полями `phone` и `address`. Используется как единственная модель пользователя (`AUTH_USER_MODEL`). |
| **forms.py** | `RegisterForm(UserCreationForm)` — регистрация с полями username, email, first_name, last_name, phone, address, пароли. `ProfileForm(ModelForm)` — редактирование имени, email, phone, address. |
| **views.py** | `register_view` — GET/POST регистрации, при успехе создаёт пользователя и вызывает `login()`, редирект на каталог. `profile_view` (только для залогиненных) — редактирование профиля. |
| **urls.py** | `login/` (LoginView), `logout/` (LogoutView), `register/`, `profile/`. Пространство имён `users`. |
| **admin.py** | Регистрация `User` в админке с расширенными полями (phone, address) в fieldsets и add_fieldsets. |
| **apps.py** | Конфиг приложения `users`. |
| **tests.py** | Проверка загрузки страниц регистрации/логина и создания пользователя при регистрации. |

Шаблоны: `users/login.html`, `users/register.html`, `users/profile.html` — форма входа, регистрации и профиля (наследуют `base.html`).

---

### 3.4 catalog/ — каталог товаров

| Файл | Назначение |
|------|------------|
| **models.py** | Модель `Product`: name, description, price, image (ImageField, upload_to='products/'), is_available, created_at. |
| **views.py** | `ProductListView` — список доступных товаров с пагинацией по 12. `product_detail_view` — одна карточка товара и последние 10 отзывов (`product.reviews`). |
| **urls.py** | `''` → список товаров (`product_list`), `product/<int:pk>/` → карточка (`product_detail`). Пространство `catalog`. |
| **admin.py** | Регистрация `Product` в админке: список с фильтром по наличию, поиск по названию и описанию. |
| **apps.py** | Конфиг приложения `catalog`. |
| **tests.py** | Проверка отображения списка и карточки товара. |

Шаблоны: `catalog/product_list.html` (сетка карточек, кнопки «В корзину» и «Подробнее»), `catalog/product_detail.html` (изображение, цена, описание, форма «В корзину», ссылка «Оставить отзыв», блок отзывов).

---

### 3.5 orders/ — заказы и корзина

| Файл | Назначение |
|------|------------|
| **models.py** | `Order`: user, status (new/confirmed/preparing/delivering/delivered/cancelled), delivery_address, delivery_phone, comment, created_at, updated_at. Свойство `total` — сумма по позициям. `OrderItem`: order, product, quantity, price (фиксируется на момент заказа). Свойство `subtotal`. |
| **cart.py** | Корзина в сессии под ключом `CART_SESSION_KEY = 'cart'`: словарь `{str(product_id): quantity}`. Функции: `get_cart`, `set_cart`, `add_to_cart`, `remove_from_cart`, `set_cart_quantity`, `clear_cart`, `get_cart_items` (список пар (Product, qty)), `get_cart_total` (сумма). |
| **context_processors.py** | Функция `cart_total(request)` возвращает словарь `cart_total` (сумма) и `cart_count` (общее количество штук) — доступны во всех шаблонах. |
| **forms.py** | `CheckoutForm`: delivery_address, delivery_phone, comment. В `__init__(user=...)` подставляет из профиля user.address и user.phone в initial. |
| **views.py** | `cart_view` — страница корзины. `cart_add` — добавление в корзину (GET, параметр quantity, next). `cart_remove`, `cart_update` — удаление и изменение количества. `checkout_view` (login_required) — форма доставки, создание Order и OrderItem, очистка корзины, вызов `send_order_to_telegram`, редирект на детали заказа. `order_list_view`, `order_detail_view` — список и детали заказов пользователя. `reorder_view` — копирование всех позиций заказа в корзину (только доступные товары). |
| **urls.py** | Маршруты: cart/, cart/add/<id>/, cart/remove/<id>/, cart/update/<id>/, checkout/, my-orders/, order/<id>/, order/<id>/reorder/. Пространство `orders`. |
| **telegram_notify.py** | `_send_telegram(text, chat_id)` — POST на `api.telegram.org/bot{token}/sendMessage` (requests). `send_order_to_telegram(order)` — форматирует текст заказа (клиент, адрес, позиции, итог) и отправляет. `send_status_to_telegram(order, old_status)` — короткое сообщение об изменении статуса. Если токен или chat_id не заданы, отправка не выполняется. |
| **signals.py** | Обработчик `pre_save` на модель `Order`: при сохранении существующего заказа сравнивает старый и новый статус; при изменении вызывает `send_status_to_telegram(instance, old.status)`. |
| **admin.py** | `Order` в админке с инлайном `OrderItem`; список с фильтрами по статусу и дате, поиск. Редактирование статуса здесь и вызывает сигнал. |
| **apps.py** | В `ready()` выполняется `import orders.signals`, чтобы зарегистрировать обработчик сигнала. |
| **tests.py** | Тесты корзины (добавление в сессию), оформления заказа (требуется логин, создаётся Order и OrderItem), повторного заказа (проверка содержимого сессии). |

Шаблоны: `orders/cart.html` (таблица позиций, изменение количества, итог, кнопки «Оформить»/«В каталог»), `orders/checkout.html` (форма доставки и блок «Состав заказа»), `orders/order_list.html` (список заказов со ссылками «Подробнее» и «Повторить заказ»), `orders/order_detail.html` (статус, адрес, состав, сумма, «Повторить заказ»).

---

### 3.6 reviews/ — отзывы и рейтинг

| Файл | Назначение |
|------|------------|
| **models.py** | Модель `Review`: user, product, text, rating (1–5), created_at. `unique_together = [['user', 'product']]` — один отзыв на пару пользователь–товар. |
| **forms.py** | `ReviewForm(ModelForm)` для полей text и rating; виджеты Textarea и Select с вариантами 1–5 ★. |
| **views.py** | `add_review` (login_required): если отзыв от этого пользователя на этот товар уже есть — редирект с предупреждением. Иначе GET — форма, POST — сохранение с подстановкой user и product, редирект на карточку товара. |
| **urls.py** | `product/<int:product_id>/add/` → add_review. Пространство `reviews`. |
| **admin.py** | Регистрация `Review` в админке. |
| **apps.py** | Конфиг приложения `reviews`. |
| **tests.py** | Проверка, что добавление отзыва требует логина и что при POST создаётся запись Review с рейтингом 5. |

Шаблон: `reviews/review_form.html` — форма текста и рейтинга с кнопками «Отправить» и «Отмена».

---

### 3.7 analytics/ — аналитика и отчёты

| Файл | Назначение |
|------|------------|
| **models.py** | Модель `Report`: date, order (FK, nullable), sales_data (JSONField), profit, expenses, created_at, created_by (User, nullable). Для хранения отчётов и связки с заказом при необходимости. |
| **views.py** | `analytics_dashboard` (staff_member_required): заказов за сегодня, всего заказов, выручка (сумма order.total по не отменённым), группировка по статусам, последние 20 заказов. `analytics_reports`: список последних 50 отчётов. |
| **urls.py** | `''` → дашборд, `reports/` → страница отчётов. Пространство `analytics`. |
| **admin.py** | Регистрация `Report` в админке. |
| **apps.py** | Конфиг приложения `analytics`. |

Шаблоны: `analytics/dashboard.html` (карточки «Заказов сегодня», «Всего заказов», «Выручка», таблицы по статусам и последние заказы со ссылками в админку), `analytics/reports.html` (таблица отчётов: дата, заказ, прибыль, расходы).

---

### 3.8 bot/ — Telegram-бот

| Файл | Назначение |
|------|------------|
| **run_bot.py** | Загружает `.env` из корня проекта, добавляет корень в `sys.path`, устанавливает `DJANGO_SETTINGS_MODULE` и вызывает `django.setup()`. Затем создаёт приложение python-telegram-bot с командами: `/start` — приветствие и список команд; `/orders` — последние 10 заказов из БД (Order.objects...); `/stats` — агрегаты (заказов сегодня, всего, выручка, по статусам). Запуск через `Application.run_polling()`. Токен берётся из окружения; при отсутствии — выход с ошибкой. |

Бот не создаёт заказы сам; заказы создаются только на сайте. Уведомления о новых заказах и смене статуса уходят с сайта через `telegram_notify` в чат с `TELEGRAM_ORDER_CHAT_ID`.

---

### 3.9 Шаблоны (templates/)

| Файл | Назначение |
|------|------------|
| **base.html** | Базовый layout: Bootstrap 5 и Bootstrap Icons с CDN, CSS-переменные (зелёная тема), навбар с ссылками на каталог, корзину (с бейджем `cart_count`), «Мои заказы», для staff — «Админ» и «Аналитика», справа — профиль/вход/регистрация. Блоки `{% block title %}`, `{% block content %}`, `{% block extra_css %}`, `{% block extra_js %}`. Вывод `messages`, footer. |
| **catalog/product_list.html** | Сетка карточек товаров (изображение или заглушка), название, описание, цена, кнопки «В корзину» и «Подробнее»; пагинация при наличии. |
| **catalog/product_detail.html** | Изображение, название, цена, описание, форма «Количество + В корзину», ссылка «Оставить отзыв» (если пользователь залогинен), блок отзывов (автор, звёзды, дата, текст). |
| **users/login.html** | Форма входа (наследует base). |
| **users/register.html** | Форма регистрации (все поля RegisterForm). |
| **users/profile.html** | Форма профиля (ProfileForm). |
| **orders/cart.html** | Таблица: товар, цена, количество (форма обновления), сумма, кнопка удаления; итог `cart_total`; кнопки «Продолжить покупки» и «Оформить заказ» (или «Войти и оформить»). |
| **orders/checkout.html** | Две колонки: форма доставки (адрес, телефон, комментарий) и блок «Состав заказа» с итогом. |
| **orders/order_list.html** | Список заказов: номер, дата, статус, ссылки «Подробнее» и «Повторить заказ». |
| **orders/order_detail.html** | Статус, дата, адрес, телефон, комментарий, таблица позиций и итог, кнопки «Повторить заказ» и «К списку заказов». |
| **reviews/review_form.html** | Форма отзыва (текст, рейтинг), кнопки «Отправить» и «Отмена». |
| **analytics/dashboard.html** | Карточки показателей, таблицы по статусам и последние заказы. |
| **analytics/reports.html** | Таблица отчётов. |

---

## 4. Связи между компонентами

- **Сессия и корзина:** только `orders.cart` и `orders.context_processors` работают с ключом `cart` в `request.session`; представления заказов вызывают функции из `cart.py`.
- **Заказы и Telegram:** создание заказа в `orders.views.checkout_view` → `send_order_to_telegram`; смена статуса в админке → `orders.signals` → `send_status_to_telegram`. Оба используют `orders.telegram_notify`.
- **Бот и БД:** бот импортирует модели после `django.setup()` и читает `Order` (и связанные данные) для `/orders` и `/stats`. Запись в БД бот не выполняет.
- **Права доступа:** страницы «Оформить заказ», «Мои заказы», детали заказа, «Повторить заказ», профиль, отзыв — только для авторизованных (`@login_required`); аналитика — только для staff (`@staff_member_required`).

---

## 5. Настройка ALLOWED_HOSTS в .env

**ALLOWED_HOSTS** — список хостов/доменов, с которых Django принимает запросы. Заголовок `Host` в каждом запросе проверяется против этого списка; при несовпадении возвращается 400. Это защита от атак с подменой Host.

### Правила настройки в .env

- **Формат:** через запятую, без кавычек. Пробелы после запятой допустимы (в коде они обрезаются).
  ```env
  ALLOWED_HOSTS=localhost,127.0.0.1
  ```
  или с пробелами:
  ```env
  ALLOWED_HOSTS=localhost, 127.0.0.1, mysite.com
  ```

- **Локальная разработка:** достаточно `localhost` и `127.0.0.1` (значение по умолчанию в проекте). Если заходите с другого имени (например, по IP в сети), добавьте его:
  ```env
  ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
  ```

- **Продакшен:** укажите реальный домен и, при необходимости, с поддоменом `www`:
  ```env
  ALLOWED_HOSTS=flowerdelivery.ru,www.flowerdelivery.ru
  ```
  Если сайт доступен и по IP сервера — добавьте и его:
  ```env
  ALLOWED_HOSTS=flowerdelivery.ru,www.flowerdelivery.ru,123.45.67.89
  ```

- **Порт в значении не указывается.** Django сравнивает только имя хоста (без порта). Запрос к `http://localhost:8000` проверяется по хосту `localhost`, порт 8000 в ALLOWED_HOSTS не нужен.

- **Подстановки:** можно использовать маску `.example.com` — тогда разрешены `example.com` и любые поддомены (`api.example.com`, `shop.example.com`). Для продакшена лучше явно перечислить нужные домены.

- **DEBUG=False:** при выключенном DEBUG список ALLOWED_HOSTS не должен быть пустым, иначе Django при запуске выдаст ошибку. В .env обязательно укажите хотя бы один хост.

### Примеры по средам

| Среда        | Пример .env |
|--------------|-------------|
| Локально     | `ALLOWED_HOSTS=localhost,127.0.0.1` |
| Сеть (по IP) | `ALLOWED_HOSTS=localhost,127.0.0.1,192.168.0.10` |
| Продакшен    | `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com` |

---

## 6. Добавление товаров на сайт

Товары (цветы, букеты) добавляются **только через админ-панель Django**. Отдельной страницы «добавить товар» для обычных пользователей на сайте нет.

### Через админку (основной способ)

1. Войти в админку под пользователем с правами **staff** или **superuser**:  
   `http://127.0.0.1:8000/admin/` (логин и пароль — от учётной записи, созданной через `createsuperuser`, или у пользователя с включённым «Статус персонала» в админке).

2. В разделе **«Каталог»** открыть **«Товары»** (или «Products»).

3. Нажать **«Добавить товар»** и заполнить:
   - **Название** — обязательно;
   - **Описание** — по желанию;
   - **Цена** — число;
   - **Изображение** — по желанию (файл сохраняется в `media/products/`);
   - **В наличии** — снятая галочка скрывает товар из каталога на сайте.

4. Сохранить — товар сразу появляется в каталоге на главной странице.

Добавлять, изменять и удалять товары могут только пользователи с правами **staff** или **superuser**.

### Альтернативы (без веб-интерфейса)

- **Через shell** — удобно для тестовых данных:
  ```bash
  python manage.py shell
  ```
  ```python
  from catalog.models import Product
  Product.objects.create(name='Букет роз', price=2500, description='25 роз')
  ```

- **Через фикстуры** — выгрузка/загрузка данных (например, `dumpdata` / `loaddata`), если нужно переносить набор товаров между окружениями.

Итог: в одном документе собраны алгоритм работы, структура проекта и пофайловое описание. Для запуска и установки см. **README.md**.
