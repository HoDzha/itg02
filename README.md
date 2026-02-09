# FlowerDelivery Master

Сайт доставки цветов с интеграцией заказов через Telegram-бота.

## Требования

- Python 3.10+
- Telegram Bot Token (создать у [@BotFather](https://t.me/BotFather))

## Установка

**Клонирование с GitHub:**

```bash
git clone https://github.com/HoDzha/itg02.git
cd itg02
```

**Создание окружения и зависимостей:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Настройка

1. Создайте файл `.env` в корне проекта (переменные загружаются через **python-dotenv**):
   - `TELEGRAM_BOT_TOKEN` — токен бота
   - `TELEGRAM_ORDER_CHAT_ID` — ID чата/группы, куда присылать новые заказы
   - `DJANGO_SECRET_KEY` — секретный ключ (обязательно в продакшене)
   - `DEBUG=True` / `False`
   
   Скопируйте `.env.example` в `.env` и заполните значения. Файл `.env` не попадает в репозиторий (см. `.gitignore`).

2. Миграции и суперпользователь (сначала `migrate` создаёт таблицы в БД, затем можно создать учётную запись администратора):

```bash
python manage.py migrate
python manage.py createsuperuser
```

   Если при `migrate` появляется ошибка **InconsistentMigrationHistory** (миграции применялись в другом порядке или с другой моделью User), удалите файл `db.sqlite3` и выполните `migrate` снова — база создастся заново с правильной схемой.

3. (Опционально) Загрузка тестовых товаров:

```bash
python manage.py shell
# from catalog.models import Product
# Product.objects.create(name='Букет роз', price=2500, description='25 роз')
```

## Запуск

**Сайт:**

```bash
python manage.py runserver
```

Откройте http://127.0.0.1:8000/

**Telegram-бот** (в отдельном терминале):

```bash
set TELEGRAM_BOT_TOKEN=ваш_токен
python -m bot.run_bot
```

Команды бота: `/start`, `/orders` (последние заказы), `/stats` (аналитика).

## Функциональность

### Веб-сайт
- Регистрация и авторизация
- Каталог цветов, корзина, оформление заказа с адресом доставки
- История заказов, повторный заказ («Повторить заказ»)
- Отзывы и рейтинг по товарам
- Админка Django: управление заказами (смена статуса), товары, отчёты
- Раздел «Аналитика» для сотрудников: выручка, заказы по статусам, отчёты

### Telegram
- Новые заказы с сайта приходят в указанный чат (текстом)
- При смене статуса заказа в админке — уведомление в Telegram
- Бот: команды `/orders` и `/stats` для просмотра заказов и аналитики

## Тестирование

```bash
python manage.py test
```

## Модели данных

- **User** (users): имя, email, телефон, адрес
- **Product** (catalog): название, цена, изображение
- **Order**, **OrderItem** (orders): заказ, позиции, статус
- **Review** (reviews): пользователь, товар, текст, рейтинг 1–5
- **Report** (analytics): дата, заказ, продажи, прибыль, расходы

## Структура проекта

- `flower_delivery/` — настройки Django
- `users/` — регистрация, авторизация, профиль
- `catalog/` — каталог товаров
- `orders/` — корзина, оформление заказа, история, повторный заказ
- `reviews/` — отзывы и рейтинги
- `analytics/` — отчёты и дашборд для сотрудников
- `bot/` — Telegram-бот

## Публикация на GitHub

Проект подготовлен к загрузке в репозиторий: в `.gitignore` исключены виртуальное окружение (`venv/`), база данных (`db.sqlite3`), файл с секретами (`.env`), загруженные медиа (`/media`), кэш Python (`__pycache__`) и служебные файлы IDE/ОС. В репозиторий попадают исходный код, миграции, шаблоны, `requirements.txt` и `.env.example` (шаблон переменных окружения без секретов).
