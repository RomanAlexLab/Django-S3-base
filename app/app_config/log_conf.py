# app_config/log_conf.py
#
# Конфигурация логгирования Django-проекта.
#
# Этот файл определяет настройки логгирования для различных компонентов проекта:
#   - Django (встроенное логирование фреймворка).
#   - Пользовательские приложения.
#   - Библиотеки boto3 и botocore.
#
# Логи записываются в два потока:
#   1. Консоль (stdout) — для отображения краткой информации.
#   2. Файл логов (`logs/logfile.log`) — для детального сохранения событий.
#
# Уровни логгирования и их назначение:
# 1. DEBUG:
#  `- Самый детальный уровень.
#   - Используется для отладки и вывода технической информации.
#   - Включает все сообщения: DEBUG, INFO, WARNING, ERROR, CRITICAL.
#
# 2. INFO:
#   - Подтверждение успешного выполнения операций.
#   - Включает сообщения уровня INFO и выше: INFO, WARNING, ERROR, CRITICAL.
#   - Сообщения уровня DEBUG игнорируются.
#
# 3. WARNING:
#   - Предупреждения о потенциальных проблемах.
#   - Включает сообщения уровня WARNING и выше: WARNING, ERROR, CRITICAL.
#   - Сообщения уровней DEBUG и INFO игнорируются.
#
# 4. ERROR:
#   - Ошибки, которые не привели к аварийному завершению программы.
#   - Включает сообщения уровня ERROR и выше: ERROR, CRITICAL.
#   - Сообщения уровней DEBUG, INFO и WARNING игнорируются.
#
# 5. CRITICAL:
#   - Критические ошибки, требующие немедленного внимания.
#   - Включает только сообщения уровня CRITICAL.
#   - Все остальные уровни (DEBUG, INFO, WARNING, ERROR) игнорируются.
#
# Путь к файлу логов:
#   - LOG_FILE = PATH_LOG_FILE
#   - PATH_LOG_FILE = BASE_DIR / 'logs' / 'logfile.log'
#   Файл автоматически создается в директории `logs` при запуске приложения,
#   это определено в файле settings.py --> LOG_FILE = PATH_LOG_FILE --> 
#   os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
#
# Обработчики:
#   - console: Выводит логи в консоль с использованием форматера `simple`.
#   - file: Записывает логи в файл с использованием форматера `verbose`.
#
# Примечание:
#   - Убедитесь, что директория `logs` существует и доступна для записи.
#   - Для корректной работы логгирования убедитесь, что переменная PATH_LOG_FILE указывает на существующий путь.


import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PATH_LOG_FILE = os.path.join(BASE_DIR, 'logs', 'logfile.log')

LOG_CONF = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': PATH_LOG_FILE,  # Путь к лог-файлу (log)
            'formatter': 'verbose',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'app_base': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'app_config': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'app_storage': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'boto3': {
            'handlers': ['console', 'file'],
            'level': 'CRITICAL',
            'propagate': True,
        },
        'botocore': {
            'handlers': ['console', 'file'],
            'level': 'CRITICAL',
            'propagate': True,
        },
    },
}