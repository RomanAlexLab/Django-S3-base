# Django-S3-base
## Шаблон Django + S3 Timeweb Cloud

> **Примечание:** Раздел находится в разработке

Это бесплатный шаблон приложения Django, который подключает S3 хранилище к вашему проекту.

### Цель данного репозитория
При подключении хранилища S3 я столкнулся с проблемой — отсутствие документации по интеграции S3 с Django в новых версиях. Поэтому я публикую этот пример как шаблон, который демонстрирует подключение S3 к админке Django и принципы работы.

В качестве хранилища S3 я использовал S3-совместимое хранилище от Timeweb Cloud. Хотя оно не полностью идентично AWS, а ткаже не поддерживает некоторые функции аутентификации, шифрования и доступа к данным, его всёже можно настроить для приватного и безопасного использования. Если вам потребуется более высокий уровень безопасности, вы можете, следуя принципам этого проекта, настроить другое S3-совместимое хранилище.

---

### Клонирование репозитория
Команды для запуска:

```bash
git clone https://github.com/RomanAlexLab/Django-S3-base.git
```

---

### Создание виртуального окружения
```bash
python -m venv venv
```

Активация виртуального окружения:

- **Linux:**
  ```bash
  source venv/bin/activate
  ```
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```

---

### Pyenv
В проекте используется Pyenv с Python 3.13.3. Если вы не используете Pyenv, возможно, потребуется удалить файл `.python-version`.  
Если вы используете Pyenv, установите Python 3.13.3:

- Установка Pyenv для Windows: [https://pypi.org/project/pyenv-win/](https://pypi.org/project/pyenv-win/)  
- Установка и работа с Pyenv для Ubuntu: [https://itshaman.ru/news/linux/ustanovka-neskolkikh-versii-python-na-ubuntu-s-pomoshchyu-pyenv](https://itshaman.ru/news/linux/ustanovka-neskolkikh-versii-python-na-ubuntu-s-pomoshchyu-pyenv)

---

### pip-tools
В проекте используется `pip-tools`. Убедитесь, что он установлен в вашем виртуальном окружении, или установите его:

```bash
pip install pip-tools
```

**Примечание:** Если появится предупреждение о необходимости обновить PIP, сделайте это перед установкой зависимостей.

---

### Зависимости
Зависимости указаны в файлах `requirements.in` (для `pip-tools`) и `requirements.txt`:

- Django==5.2.3
- dotenv==0.9.9
- pillow==11.2.1
- boto3==1.38.46
- django-storages[s3]==1.14.6
- django-csp==4.0

Команда установки зависисмостей:
```bash
pip-sync
```

---

### Конфигурация проекта
В файле `.env` укажите секретный ключ Django и настройки S3 от Timeweb Cloud.

В директорию с файлом `settings.py` добавьте следующие файлы:  
- `const_conf.py` — Константы  
- `cors_conf.py` — Настройка CORS вашего приложения  
- `log_conf.py` — Настройки логирования  
- `s3_conf.py` — Конфигурация и настройка S3 хранилища (основной файл)  

---

### settings.py
Выполните необходимые импорты.

Подгрузите переменные окружения:
```python
load_dotenv()
```

```python
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
```

#### Режим разработки
```python
MODE_DEV = False
```

#### Настройка логирования
```python
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if MODE_DEV else False

# Создание директорий и logfile + путь до logfile
LOG_FILE = PATH_LOG_FILE
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Указываем, как обрабатывать наш словарь логирования
LOGGING_CONFIG = 'logging.config.dictConfig'

# Делаем глубокую копию конфигурации логирования
LOGGING = copy.deepcopy(LOG_CONF)

# Задаём реальный путь к файлу логов
LOGGING['handlers']['file']['filename'] = LOG_FILE

# Если DEBUG выключен — меняем уровень всех логгеров на ERROR
if not DEBUG:
    for logger in LOGGING['loggers'].values():
        logger['level'] = 'ERROR'
```

#### Разрешённые Hosts
```python
ALLOWED_HOSTS = G_ALLOWED_HOSTS_LIST
```

#### Content-Security-Policy (CSP)
```python
MAIN_DOMAIN = CORS_MAIN_DOMAIN
CSP_DEFAULT_SRC = CORS_CSP_DEFAULT_SRC
CSP_INCLUDE_NONCE_IN = CORS_CSP_INCLUDE_NONCE_IN
CSP_SCRIPT_SRC = CORS_CSP_SCRIPT_SRC
CSP_STYLE_SRC = CORS_CSP_STYLE_SRC
CSP_IMG_SRC = CORS_CSP_IMG_SRC
CSP_FONT_SRC = CORS_CSP_FONT_SRC
CSP_CONNECT_SRC = CORS_CSP_CONNECT_SRC
CSP_OBJECT_SRC = CORS_CSP_OBJECT_SRC
CSP_MEDIA_SRC = CORS_CSP_MEDIA_SRC
CSP_FRAME_SRC = CORS_CSP_FRAME_SRC
CSP_BASE_URI = CORS_CSP_BASE_URI
CSP_FORM_ACTION = CORS_CSP_FORM_ACTION
CSP_MANIFEST_SRC = CORS_CSP_MANIFEST_SRC
```

#### Application
```python
INSTALLED_APPS = [
    ...
    'storages',
    'app_storage',
]
```

#### Middleware
```python
MIDDLEWARE = [
    ...
    'csp.middleware.CSPMiddleware',
]
```

#### Основной файл маршрутизации URL-адресов (URLconf)
```python
ROOT_URLCONF = 'app_config.urls'
```

#### Директории HTML-шаблонов
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

#### Internationalization
```python
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
```

#### Хранилище и файлы

##### Static files (CSS, JavaScript, Images)
```python
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Локальные директории со статикой (где Django ищет статику при сборке)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

if MODE_DEV:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATIC_URL = '/static/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'
else:
    # Локальные директории, куда складывается собранная статика или
    # загружаются пользовательские файлы (при работе с S3 не используется)
    # DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    # STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

    # Конфигурация S3
    STORAGES = STORAGES_CONF

    # Ссылки на директории с файлами (откуда Django берёт пути при формировании ссылок на файлы)
    # Если при работе с S3 используются свои конфигурации для медиафайлов,
    # то MEDIA_URL не используется, но оставлен как значение по умолчанию.
    STATIC_URL = f"https://{S3Data.AWS_S3_CUSTOM_DOMAIN}/static/"
    MEDIA_URL = f"https://{S3Data.AWS_S3_CUSTOM_DOMAIN}/media/"
```

---

### Запуск проекта
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py runserver
```

---

## 📧 Как связаться со мной

Если у вас есть вопросы, предложения или вы хотите обсудить сотрудничество, вы можете связаться со мной через:


-  **Vk:** [Профиль Vk](https://vk.com/roman2019alex)

-  **Telegram:** [@Roman89n](https://t.me/Roman89n)