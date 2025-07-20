from django.apps import AppConfig


class AppStorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_storage'
    verbose_name = 'Хранилище'

    def ready(self):
        # Подключаем сигналы
        import app_storage.signals
