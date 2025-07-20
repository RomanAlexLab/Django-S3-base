# app_storage/admin.py
#
# Этот файл содержит настройки административной панели Django для моделей,
# связанных с хранением медиафайлов (изображений, видео, документов) в S3-хранилище.
#
# Поддерживает:
# - Отображение информации о файлах: название, ссылка, размер, каталог
# - Кастомную пагинацию в админке
# - Удаление файлов из S3 при удалении объектов модели
# - Генерацию временных ссылок для просмотра файлов
#
# Все модели используют два типа хранилищ:
# - StoragesConf.get_storage_conf_1() — для приватных файлов
# - StoragesConf.get_storage_conf_2() — для публичных файлов
#
# Для каждой модели реализованы:
# - Форма редактирования
# - Пользовательские действия (например, массовое удаление)
# - Отображение ссылок с поддержкой предпросмотра в модальном окне
# - Обработка ошибок при работе с S3


import os
import logging
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import ValidationError
from .forms import (
    PublicImageForm, PublicVideoForm, PublicFileForm,
    PrivateVideoForm, PrivateImageForm, PrivateFileForm, MediaFileForm
)
from .models import (
    PublicImage, PublicVideo, PublicFile,
    PrivateImage, PrivateVideo, PrivateFile, MediaFile
)
from app_config.s3_conf import S3Data, StoragesConf
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError


logger = logging.getLogger(__name__)


class CustomChangeList(ChangeList):
    """Кастомный класс ChangeList для управления списком(кол-вом) объектов в админке."""

    def __init__(self, request, *args, **kwargs):
        # Сохраняем параметр limit из GET-запроса
        self.limit = request.GET.get('limit')
        super().__init__(request, *args, **kwargs)
        # Отключаем возможность показа всех записей
        self.can_show_all = False

    def get_filters_params(self, params=None):
        """
        Исключает параметр limit из параметров фильтрации.
        Args:
            params: Параметры запроса (опционально).
        Returns:
            dict: Отфильтрованные параметры без limit.
        """
        lookup_params = super().get_filters_params(params)
        lookup_params.pop('limit', None)
        return lookup_params

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        # Добавляет limit в параметры, если он есть
        if self.limit and 'limit' not in new_params:
            new_params['limit'] = self.limit
        return super().get_query_string(new_params, remove)


class CustomModelAdmin(admin.ModelAdmin):
    """Базовый класс администратора с кастомной пагинацией и шаблоном."""

    list_per_page = 20                                              # Количество элементов на странице по умолчанию
    list_max_show_all = 60                                          # Максимальное количество элементов
    change_list_template = 'admin/app_storage/change_list.html'     # Кастомный шаблон (выбор кол-ва элементов для отображения на старнице)

    def get_changelist(self, request, **kwargs):
        """
        Возвращает кастомный класс ChangeList.
        Args:
            request: HTTP-запрос.
            **kwargs: Дополнительные аргументы.
        Returns:
            type: Класс CustomChangeList.
        """
        return CustomChangeList

    def get_changelist_instance(self, request):
        """
        Устанавливает list_per_page на основе параметра limit.
        Args:
            request: HTTP-запрос.
        Returns:
            ChangeList: Экземпляр кастомного ChangeList.
        """
        raw = request.GET.get('limit')
        try:
            limit = int(raw) if raw is not None else self.list_per_page
            if not (1 <= limit <= self.list_max_show_all):
                raise ValueError('limit вне допустимого диапазона')
        except (TypeError, ValueError) as e:
            logger.warning(f"Некорректный параметр limit: {raw}. Используется значение по умолчанию {self.list_per_page}. ({e})")
            limit = self.list_per_page
        self.list_per_page = limit
        return super().get_changelist_instance(request)

    def changelist_view(self, request, extra_context=None):
        """
        Добавляет контекст для отображения вариантов лимита записей на странице.
        Args:
            request: HTTP-запрос.
            extra_context: Дополнительный контекст (опционально).
        Returns:
            HttpResponse: Ответ с отрендеренным шаблоном.
        """
        extra_context = extra_context or {}
        extra_context['page_sizes'] = [20, 40, 60]
        extra_context['selected_limit'] = self.list_per_page
        return super().changelist_view(request, extra_context=extra_context)


# =============================
# Регистрация моделей в админке
# =============================


# ------------------------
# Публичные модели и файлы
# ------------------------


@admin.register(PublicImage)
class PublicImageAdmin(CustomModelAdmin):
    """Админка для модели PublicImage с кастомным отображением и действиями."""

    form = PublicImageForm                                          # Форма создания/редактирования объектов
    list_display = ('name', 'link', 'file_size', 'uploaded_at')     # Поля отображения
    actions = ['delete_selected_objects_and_files']                 # Действия

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StoragesConf.get_storage_conf_2()

    def link(self, obj):
        """
        Генерирует ссылку для просмотра изображения с учетом типа файла.
        Args:
            obj: Объект PublicImage.
        Returns:
            str: HTML-код ссылки или дефис, если изображение отсутствует.
        """
        if not obj.image:
            return '-'
        key = obj.image.name
        try:
            url = self.storage.url(key, expire=S3Data.DEFAULT_LINK_EXPIRATION)
        except Exception as e:
            logger.error(f"Ошибка при генерации ссылки PublicImage {obj.id}: {e}")
            return '-'
        ext = os.path.splitext(key.lower())[1]
        file_type = 'image' if ext in S3Data.IMAGE_FILE_TYPES else 'unknown'
        mime = S3Data.IMAGE_MIME_TYPES.get(ext, 'application/octet-stream')
        return format_html(
            '<a href="#" data-media="true" data-url="{}" data-file-type="{}" data-mime-type="{}" data-filename="{}">Посмотреть</a>',
            url, file_type, mime, obj.name
        )
    
    link.short_description = 'Ссылка'

    def file_size(self, obj):
        """
        Возвращает размер файла в килобайтах.
        Args:
            obj: Объект PublicImage.
        Returns:
            str: Размер файла в KB или дефис, если файл отсутствует.
        """
        if obj.image and obj.image.size:
            return f"{obj.image.size/1024:.2f} KB"
        return '-'
    
    file_size.short_description = 'Размер'

    def uploaded_at(self, obj):
        """
        Возвращает имя файла как индикатор каталога.
        Args:
            obj: Объект PublicImage.
        Returns:
            str: Имя файла или дефис, если файл отсутствует.
        """
        return obj.image.name or '-'
    
    uploaded_at.short_description = 'Каталог'

    def delete_selected_objects_and_files(self, request, queryset):
        """
        Удаляет выбранные объекты и связанные с ними файлы из хранилища.
        Args:
            request: HTTP-запрос.
            queryset: Набор объектов для удаления.
        """
        for obj in queryset:
            key = getattr(obj, 'image', None) and obj.image.name
            try:
                exists = False
                try:
                    exists = self.storage.exists(key)
                except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                    logger.warning(f"Не удалось проверить существование {key}: {e}")
                if exists:
                    try:
                        self.storage.delete(key)
                        logger.info(f"Удалено изображение {key}")
                    except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                        logger.error(f"Не удалось удалить S3-объект {key}: {e}")
                obj.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении PublicImage {obj.id}: {e}")
                self.message_user(request, f"Ошибка при удалении {obj.id}: {e}", level='ERROR')
        self.message_user(request, "Выбранные изображения успешно удалены.", level='SUCCESS')
    
    delete_selected_objects_and_files.short_description = "Удалить выделенные файлы"


@admin.register(PublicVideo)
class PublicVideoAdmin(CustomModelAdmin):
    """Админка для модели PublicVideo с кастомным отображением и действиями."""

    form = PublicVideoForm                                          # Форма создания/редактирования объектов
    list_display = ('name', 'link', 'file_size', 'uploaded_at')     # Поля отображени
    actions = ['delete_selected_objects_and_files']                 # Действия

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StoragesConf.get_storage_conf_2()

    def link(self, obj):
        """
        Генерирует ссылку для просмотра видео с учетом типа файла.
        Args:
            obj: Объект PublicVideo.
        Returns:
            str: HTML-код ссылки или дефис, если видео отсутствует.
        """
        if not obj.video:
            return '-'
        key = obj.video.name
        try:
            url = self.storage.url(key, expire=S3Data.DEFAULT_LINK_EXPIRATION)
        except Exception as e:
            logger.error(f"Ошибка при генерации ссылки PublicVideo {obj.id}: {e}")
            return '-'
        ext = os.path.splitext(key.lower())[1]
        file_type = 'video' if ext in S3Data.VIDEO_FILE_TYPES else 'unknown'
        mime = S3Data.VIDEO_MIME_TYPES.get(ext, 'application/octet-stream')
        return format_html(
            '<a href="#" data-media="true" data-url="{}" data-file-type="{}" data-mime-type="{}" data-filename="{}">Посмотреть</a>',
            url, file_type, mime, obj.name
        )
    
    link.short_description = 'Ссылка'

    def file_size(self, obj):
        """
        Возвращает размер видео в килобайтах.
        Args:
            obj: Объект PublicVideo.
        Returns:
            str: Размер файла в KB или дефис, если видео отсутствует.
        """
        if obj.video and obj.video.size:
            return f"{obj.video.size/1024:.2f} KB"
        return '-'
    file_size.short_description = 'Размер'

    def uploaded_at(self, obj):
        """
        Возвращает имя файла как индикатор каталога.
        Args:
            obj: Объект PublicVideo.
        Returns:
            str: Имя файла или дефис, если видео отсутствует.
        """
        return obj.video.name or '-'
    uploaded_at.short_description = 'Каталог'

    def delete_selected_objects_and_files(self, request, queryset):
        """
        Удаляет выбранные объекты и связанные с ними видео из хранилища.
        Args:
            request: HTTP-запрос.
            queryset: Набор объектов для удаления.
        """
        for obj in queryset:
            key = getattr(obj, 'video', None) and obj.video.name
            try:
                exists = False
                try:
                    exists = self.storage.exists(key)
                except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                    logger.warning(f"Не удалось проверить существование {key}: {e}")
                if exists:
                    try:
                        self.storage.delete(key)
                        logger.info(f"Удалено видео {key}")
                    except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                        logger.error(f"Не удалось удалить S3-объект {key}: {e}")
                obj.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении PublicVideo {obj.id}: {e}")
                self.message_user(request, f"Ошибка при удалении {obj.id}: {e}", level='ERROR')
        self.message_user(request, "Выбранные видео успешно удалены.", level='SUCCESS')
    
    delete_selected_objects_and_files.short_description = "Удалить выделенные файлы"


@admin.register(PublicFile)
class PublicFileAdmin(CustomModelAdmin):
    """Админка для модели PublicFile с кастомным отображением и действиями."""

    form = PublicFileForm                                           # Форма создания/редактирования объектов
    list_display = ('name', 'link', 'file_size', 'uploaded_at')     # Поля отображения
    actions = ['delete_selected_objects_and_files']                 # Действия

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StoragesConf.get_storage_conf_2()

    def link(self, obj):
        """
        Генерирует ссылку для просмотра документа с учетом типа файла.
        Args:
            obj: Объект PublicFile.
        Returns:
            str: HTML-код ссылки или дефис, если файл отсутствует.
        """
        if not obj.file:
            return '-'

        key = obj.file.name
        try:
            url = self.storage.url(key, expire=S3Data.DEFAULT_LINK_EXPIRATION)
        except Exception as e:
            logger.error(f"Ошибка при генерации ссылки PublicFile {obj.id}: {e}")
            return '-'

        ext = os.path.splitext(key.lower())[1]
        file_type = next(
            (ftype for extensions, ftype in S3Data.ALL_FILE_TYPES.items() if ext in extensions),
            'unknown'
        )
        mime = S3Data.ALL_MIME_TYPES.get(ext, 'application/octet-stream')

        if file_type == 'file':
            return format_html(
                '<a href="{}" target="_blank" data-mime-type="{}">Посмотреть</a>',
                url, mime
            )
        return format_html(
            '<a href="#" data-media="true" data-url="{}" data-file-type="{}" data-mime-type="{}" data-filename="{}">Посмотреть</a>',
            url, file_type, mime, obj.name
        )
    
    link.short_description = 'Ссылка'

    def file_size(self, obj):
        """
        Возвращает размер файла в килобайтах.
        Args:
            obj: Объект PublicFile.
        Returns:
            str: Размер файла в KB или дефис, если файл отсутствует.
        """
        if obj.file and obj.file.size:
            return f"{obj.file.size / 1024:.2f} KB"
        return '-'
    
    file_size.short_description = 'Размер'

    def uploaded_at(self, obj):
        """
        Возвращает имя файла как индикатор каталога.
        Args:
            obj: Объект PublicFile.
        Returns:
            str: Имя файла или дефис, если файл отсутствует.
        """
        return obj.file.name if obj.file and obj.file.name else '-'
    
    uploaded_at.short_description = 'Каталог'

    def delete_selected_objects_and_files(self, request, queryset):
        """
        Удаляет выбранные объекты и связанные с ними файлы из хранилища.
        Args:
            request: HTTP-запрос.
            queryset: Набор объектов для удаления.
        """
        for obj in queryset:
            key = getattr(obj, 'file', None) and obj.file.name
            try:
                exists = False
                try:
                    exists = self.storage.exists(key)
                except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                    logger.warning(f"Не удалось проверить существование {key}: {e}")
                if exists:
                    try:
                        self.storage.delete(key)
                        logger.info(f"Удалён файл: {key}")
                    except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                        logger.error(f"Не удалось удалить S3-объект {key}: {e}")
                obj.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении PublicFile {obj.id}: {e}")
                self.message_user(request, f"Ошибка при удалении {obj.id}: {e}", level='ERROR')
        self.message_user(request, "Выбранные файлы успешно удалены.", level='SUCCESS')

    delete_selected_objects_and_files.short_description = 'Удалить выделенные файлы'


# ------------------------
# Приватные модели и файлы
# ------------------------


@admin.register(PrivateImage)
class PrivateImageAdmin(CustomModelAdmin):
    """Админка для модели PrivateImage с кастомным отображением и действиями."""

    form = PrivateImageForm                                         # Форма создания/редактирования объектов
    list_display = ('name', 'link', 'file_size', 'uploaded_at')     # Поля отображения
    actions = ['delete_selected_objects_and_files']                 # Действия

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StoragesConf.get_storage_conf_1()

    def link(self, obj):
        """
        Генерирует ссылку для просмотра изображения с учетом типа файла.
        Args:
            obj: Объект PrivateImage.
        Returns:
            str: HTML-код ссылки или дефис, если изображение отсутствует.
        """
        if not obj.image:
            return '-'
        key = obj.image.name
        try:
            url = self.storage.url(key, expire=S3Data.DEFAULT_LINK_EXPIRATION)
        except Exception as e:
            logger.error(f"Ошибка при генерации ссылки PrivateImage {obj.id}: {e}")
            return '-'
        ext = os.path.splitext(key.lower())[1]
        file_type = 'image' if ext in S3Data.IMAGE_FILE_TYPES else 'unknown'
        mime = S3Data.IMAGE_MIME_TYPES.get(ext, 'application/octet-stream')
        return format_html(
            '<a href="#" data-media="true" data-url="{}" data-file-type="{}" data-mime-type="{}" data-filename="{}">Посмотреть</a>',
            url, file_type, mime, obj.name
        )
    
    link.short_description = 'Ссылка'

    def file_size(self, obj):
        """
        Возвращает размер изображения в килобайтах.
        Args:
            obj: Объект PrivateImage.
        Returns:
            str: Размер файла в KB или дефис, если изображение отсутствует.
        """
        if obj.image and obj.image.size:
            return f"{obj.image.size / 1024:.2f} KB"
        return "-"

    file_size.short_description = "Размер"

    def uploaded_at(self, obj):
        """
        Возвращает имя файла как индикатор каталога.
        Args:
            obj: Объект PrivateImage.
        Returns:
            str: Имя файла или дефис, если изображение отсутствует.
        """
        if obj.image and obj.image.name:
            return obj.image.name
        return "-"

    uploaded_at.short_description = "Каталог"

    def delete_selected_objects_and_files(self, request, queryset):
        """
        Удаляет выбранные объекты и связанные с ними файлы из хранилища.
        Args:
            request: HTTP-запрос.
            queryset: Набор объектов для удаления.
        """
        for obj in queryset:
            key = getattr(obj, 'image', None) and obj.image.name
            try:
                exists = False
                try:
                    exists = self.storage.exists(key)
                except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                    logger.warning(f"Не удалось проверить существование {key}: {e}")
                if exists:
                    try:
                        self.storage.delete(key)
                        logger.info(f"Удалено изображение {key}")
                    except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                        logger.error(f"Не удалось удалить S3-объект {key}: {e}")
                obj.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении PrivateImage {obj.id}: {e}")
                self.message_user(request, f"Ошибка при удалении {obj.id}: {e}", level='ERROR')
        self.message_user(request, "Выбранные изображения успешно удалены.", level='SUCCESS')
    
    delete_selected_objects_and_files.short_description = "Удалить выделенные файлы"


@admin.register(PrivateVideo)
class PrivateVideoAdmin(CustomModelAdmin):
    """Админка для модели PrivateVideo с кастомным отображением и действиями."""

    form = PrivateVideoForm                                         # Форма создания/редактирования объектов
    list_display = ('name', 'link', 'file_size', 'uploaded_at')     # Поля отображения
    actions = ['delete_selected_objects_and_files']                 # Действия

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StoragesConf.get_storage_conf_1()

    def link(self, obj):
        """
        Генерирует ссылку для просмотра видео с учетом типа файла.
        Args:
            obj: Объект PrivateVideo.
        Returns:
            str: HTML-код ссылки или дефис, если видео отсутствует.
        """
        if not obj.video:
            return '-'
        key = obj.video.name
        try:
            url = self.storage.url(key, expire=S3Data.DEFAULT_LINK_EXPIRATION)
        except Exception as e:
            logger.error(f"Ошибка при генерации ссылки PrivateVideo {obj.id}: {e}")
            return '-'
        ext = os.path.splitext(key.lower())[1]
        file_type = 'video' if ext in S3Data.VIDEO_FILE_TYPES else 'unknown'
        mime = S3Data.VIDEO_MIME_TYPES.get(ext, 'application/octet-stream')
        return format_html(
            '<a href="#" data-media="true" data-url="{}" data-file-type="{}" data-mime-type="{}" data-filename="{}">Посмотреть</a>',
            url, file_type, mime, obj.name
        )
    
    link.short_description = 'Ссылка'

    def file_size(self, obj):
        """
        Возвращает размер видео в килобайтах.
        Args:
            obj: Объект PrivateVideo.
        Returns:
            str: Размер файла в KB или дефис, если видео отсутствует.
        """
        if obj.video and obj.video.size:
            return f"{obj.video.size / 1024:.2f} KB"
        return "-"

    file_size.short_description = "Размер"

    def uploaded_at(self, obj):
        """
        Возвращает имя файла как индикатор каталога.
        Args:
            obj: Объект PrivateVideo.
        Returns:
            str: Имя файла или дефис, если видео отсутствует.
        """
        if obj.video and obj.video.name:
            return obj.video.name
        return "-"

    uploaded_at.short_description = "Каталог"

    def delete_selected_objects_and_files(self, request, queryset):
        """
        Удаляет выбранные объекты и связанные с ними видео из хранилища.
        Args:
            request: HTTP-запрос.
            queryset: Набор объектов для удаления.
        """
        for obj in queryset:
            key = getattr(obj, 'video', None) and obj.video.name
            try:
                exists = False
                try:
                    exists = self.storage.exists(key)
                except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                    logger.warning(f"Не удалось проверить существование {key}: {e}")
                if exists:
                    try:
                        self.storage.delete(key)
                        logger.info(f"Удалено видео {key}")
                    except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                        logger.error(f"Не удалось удалить S3-объект {key}: {e}")
                obj.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении PrivateVideo {obj.id}: {e}")
                self.message_user(request, f"Ошибка при удалении {obj.id}: {e}", level='ERROR')
        self.message_user(request, "Выбранные видео успешно удалены.", level='SUCCESS')
    
    delete_selected_objects_and_files.short_description = "Удалить выделенные файлы"


@admin.register(PrivateFile)
class PrivateFileAdmin(CustomModelAdmin):
    """Админка для модели PrivateFile с кастомным отображением и действиями."""

    form = PrivateFileForm                                          # Форма создания/редактирования объектов
    list_display = ('name', 'link', 'file_size', 'uploaded_at')     # Поля отображения
    actions = ['delete_selected_objects_and_files']                 # Действия

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StoragesConf.get_storage_conf_1()

    def link(self, obj):
        """
        Генерирует ссылку для просмотра документа с учетом типа файла.
        Args:
            obj: Объект PrivateFile.
        Returns:
            str: HTML-код ссылки или дефис, если файл отсутствует.
        """
        if not obj.file:
            return '-'

        key = obj.file.name
        try:
            url = self.storage.url(key, expire=S3Data.DEFAULT_LINK_EXPIRATION)
        except Exception as e:
            logger.error(f"Ошибка при генерации ссылки PrivateFile {obj.id}: {e}")
            return '-'

        ext = os.path.splitext(key.lower())[1]
        file_type = next(
            (ftype for extensions, ftype in S3Data.ALL_FILE_TYPES.items() if ext in extensions),
            'unknown'
        )
        mime = S3Data.ALL_MIME_TYPES.get(ext, 'application/octet-stream')

        if file_type == 'file':
            return format_html(
                '<a href="{}" target="_blank" data-mime-type="{}">Посмотреть</a>',
                url, mime
            )
        return format_html(
            '<a href="#" data-media="true" data-url="{}" data-file-type="{}" data-mime-type="{}" data-filename="{}">Посмотреть</a>',
            url, file_type, mime, obj.name
        )
    
    link.short_description = 'Ссылка'

    def file_size(self, obj):
        """
        Возвращает размер файла в килобайтах.
        Args:
            obj: Объект PrivateFile.
        Returns:
            str: Размер файла в KB или дефис, если файл отсутствует.
        """
        if obj.file and obj.file.size:
            return f"{obj.file.size / 1024:.2f} KB"
        return "-"

    file_size.short_description = "Размер"

    def uploaded_at(self, obj):
        """
        Возвращает имя файла как индикатор каталога.
        Args:
            obj: Объект PrivateFile.
        Returns:
            str: Имя файла или дефис, если файл отсутствует.
        """
        if obj.file and obj.file.name:
            return obj.file.name
        return "-"

    uploaded_at.short_description = "Каталог"

    def delete_selected_objects_and_files(self, request, queryset):
        """
        Удаляет выбранные объекты и связанные с ними файлы из хранилища.
        Args:
            request: HTTP-запрос.
            queryset: Набор объектов для удаления.
        """
        for obj in queryset:
            key = getattr(obj, 'file', None) and obj.file.name
            try:
                exists = False
                try:
                    exists = self.storage.exists(key)
                except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                    logger.warning(f"Не удалось проверить существование {key}: {e}")
                if exists:
                    try:
                        self.storage.delete(key)
                        logger.info(f"Удалён файл: {key}")
                    except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                        logger.error(f"Не удалось удалить S3-объект {key}: {e}")
                obj.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении PrivateFile {obj.id}: {e}")
                self.message_user(request, f"Ошибка при удалении {obj.id}: {e}", level='ERROR')
        self.message_user(request, "Выбранные файлы успешно удалены.", level='SUCCESS')

    delete_selected_objects_and_files.short_description = 'Удалить выделенные файлы'


@admin.register(MediaFile)
class MediaFileAdmin(CustomModelAdmin):
    """Админка для модели MediaFile с кастомным отображением и действиями."""

    form = MediaFileForm                                            # Форма создания/редактирования объектов
    list_display = ('name', 'link', 'file_size', 'uploaded_at')     # Поля отображения
    actions = ['delete_selected_objects_and_files']                 # Действия

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StoragesConf.get_storage_conf_1()

    def link(self, obj):
        """
        Генерирует ссылку для просмотра документа с учетом типа файла.
        Args:
            obj: Объект MediaFile.
        Returns:
            str: HTML-код ссылки или дефис, если файл отсутствует.
        """
        if not obj.file:
            return '-'

        key = obj.file.name
        try:
            url = self.storage.url(key, expire=S3Data.DEFAULT_LINK_EXPIRATION)
        except Exception as e:
            logger.error(f"Ошибка при генерации ссылки MediaFile {obj.id}: {e}")
            return '-'

        ext = os.path.splitext(key.lower())[1]
        file_type = next(
            (ftype for extensions, ftype in S3Data.ALL_FILE_TYPES.items() if ext in extensions),
            'unknown'
        )
        mime = S3Data.ALL_MIME_TYPES.get(ext, 'application/octet-stream')

        if file_type == 'file':
            return format_html(
                '<a href="{}" target="_blank" data-mime-type="{}">Посмотреть</a>',
                url, mime
            )
        return format_html(
            '<a href="#" data-media="true" data-url="{}" data-file-type="{}" data-mime-type="{}" data-filename="{}">Посмотреть</a>',
            url, file_type, mime, obj.name
        )
    
    link.short_description = 'Ссылка'

    def file_size(self, obj):
        """
        Возвращает размер файла в килобайтах.
        Args:
            obj: Объект MediaFile.
        Returns:
            str: Размер файла в KB или дефис, если файл отсутствует.
        """
        if obj.file and obj.file.size:
            return f"{obj.file.size / 1024:.2f} KB"
        return "-"

    file_size.short_description = "Размер"

    def uploaded_at(self, obj):
        """
        Возвращает имя файла как индикатор каталога.
        Args:
            obj: Объект MediaFile.
        Returns:
            str: Имя файла или дефис, если файл отсутствует.
        """
        if obj.file and obj.file.name:
            return obj.file.name
        return "-"

    uploaded_at.short_description = "Каталог"

    def delete_selected_objects_and_files(self, request, queryset):
        """
        Удаляет выбранные объекты и связанные с ними файлы из хранилища.
        Args:
            request: HTTP-запрос.
            queryset: Набор объектов для удаления.
        """
        for obj in queryset:
            key = getattr(obj, 'file', None) and obj.file.name
            try:
                exists = False
                try:
                    exists = self.storage.exists(key)
                except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                    logger.warning(f"Не удалось проверить существование {key}: {e}")
                if exists:
                    try:
                        self.storage.delete(key)
                        logger.info(f"Удалён файл: {key}")
                    except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
                        logger.error(f"Не удалось удалить S3-объект {key}: {e}")
                obj.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении MediaFile {obj.id}: {e}")
                self.message_user(request, f"Ошибка при удалении {obj.id}: {e}", level='ERROR')
        self.message_user(request, "Выбранные файлы успешно удалены.", level='SUCCESS')

    delete_selected_objects_and_files.short_description = 'Удалить выделенные файлы'