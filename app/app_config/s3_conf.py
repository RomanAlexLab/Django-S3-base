# app_config/s3_conf.py

"""
Конфигурация для работы с облачным хранилищем S3 (Timeweb Cloud).

Этот файл содержит настройки и классы для интеграции Django с S3-хранилищем.
Основная цель — управление медиа- и статическими файлами, включая их загрузку,
валидацию и доступ.

Основные компоненты:
1. **S3Data**:
   - Класс, содержащий константы и настройки для работы с S3.
   - Включает параметры подключения (ключи доступа, URL, регион),
     ограничения на размеры файлов, разрешённые MIME-типы и расширения,
     а также конфигурацию передачи данных.

2. **STORAGES_CONF**:
   - Конфигурация хранилищ для Django.
   - Определяет два типа хранилищ:
     - `default`: Для медиа-файлов с приватным доступом.
     - `staticfiles`: Для статических файлов с публичным доступом.

3. **CustomS3Storage**:
   - Кастомное хранилище, унаследованное от S3Storage.
   - Добавляет функциональность для проверки MIME-типов, расширений файлов,
     управления кэшированием и сжатием (gzip).
   - Обеспечивает корректную обработку ошибок при загрузке файлов.

4. **StoragesConf**:
   - Класс для получения экземпляров хранилищ с различными настройками:
     - `get_storage_conf_1`: Приватное хранилище (с временной авторизацией).
     - `get_storage_conf_2`: Публичное хранилище (открытый доступ).

Особенности реализации:
- Используется библиотека boto3 для взаимодействия с S3.
- Реализована валидация файлов по размеру и расширению.
- Поддерживается автоматическое определение MIME-типов на основе расширений.
- Настроено логирование для отслеживания ошибок и предупреждений.

Примечание:
- Переменные окружения загружаются из файла `.env`.
- Необходимо убедиться, что все обязательные переменные окружения установлены.

Документация:
django-storages:
- https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
object_parameters:
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html#
client_config:
- https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config
"""

import os
import mimetypes
import logging
from pathlib import Path
from dotenv import load_dotenv
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
from boto3.s3.transfer import TransferConfig
from storages.backends.s3 import S3Storage
from storages.utils import clean_name, is_seekable, ReadBytesWrapper
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)


if not load_dotenv():
    logger.error("Не удалось загрузить файл .env. Проверьте его наличие и корректность.")
    raise EnvironmentError("Не удалось загрузить переменные окружения из .env файла")


# Проверка наличия обязательных переменных
required_env_vars = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_REGION_NAME",
    "AWS_S3_ENDPOINT_URL",
]
for var in required_env_vars:
    if not os.getenv(var):
        logger.error(f"Переменная окружения {var} не установлена.")
        raise EnvironmentError(f"Переменная окружения {var} не установлена.")


# == Конфигурация S3 (Timeweb Cloud) ==


KB = 1024
MB = KB * KB


# Категоризация типов файлов
G_ALL_FILE_TYPES = (
    '.md', '.txt', '.pdf', '.html', '.htm', '.css', '.js', '.json', '.map',
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
    '.mp4', '.webm', '.ogg', '.mov',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz',
    '.tar.gz', '.tbz', '.tbz2', '.tar.bz2', '.txz', '.tar.xz',
    '.xls', '.xlsx', '.xlsm', '.ods', '.csv', '.tsv', '.xlsb', '.xlt', '.xltm', '.xltx',
    '.numbers', '.prn', '.slk', '.parquet', '.feather', '.orc',
    '',
)
G_OCSET_STREAM_FILE_TYPES = ('',)
G_TABLE_FILE_TYPES = (
    '.xls', '.xlsx', '.xlsm', '.ods', '.csv', '.tsv', '.xlsb', '.xlt', '.xltm', '.xltx',
    '.numbers', '.prn', '.slk', '.parquet', '.feather', '.orc',
)
G_ARCH_FILE_TYPES = (
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz',
    '.tar.gz', '.tbz', '.tbz2', '.tar.bz2', '.txz', '.tar.xz',
)
G_DOCS_FILE_TYPES = ('.md', '.txt', '.pdf', '.html', '.htm', '.css', '.js', '.json', '.map',)
G_IMAGE_FILE_TYPES = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico')
G_VIDEO_FILE_TYPES = ('.mp4', '.webm', '.ogg', '.mov')


# MIME-типы для всех расширений
G_ALL_MIME_TYPES = {
    # Текстовые и прочие
    '.md': 'text/markdown',
    '.txt': 'text/plain',
    '.pdf': 'application/pdf',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.map': 'application/json',

    # Изображения
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',

    # Видео
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.ogg': 'video/ogg',
    '.mov': 'video/quicktime',

    # Архивы
    '.zip': 'application/zip',
    '.rar': 'application/x-rar-compressed',
    '.7z': 'application/x-7z-compressed',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    '.bz2': 'application/x-bzip2',
    '.xz': 'application/x-xz',
    '.tgz': 'application/gzip',
    '.tar.gz': 'application/gzip',
    '.tbz': 'application/x-bzip2',
    '.tbz2': 'application/x-bzip2',
    '.tar.bz2': 'application/x-bzip2',
    '.txz': 'application/x-xz',
    '.tar.xz': 'application/x-xz',

    # Табличные форматы (добавленные)
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xlsm': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
    '.csv': 'text/csv',
    '.tsv': 'text/tab-separated-values',
    '.xlsb': 'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
    '.xlt': 'application/vnd.ms-excel',
    '.xltx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
    '.xltm': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
    '.numbers': 'application/x-iwork-numbers-sffnumbers',
    '.prn': 'application/octet-stream',
    '.slk': 'application/vnd.slink',
    '.parquet': 'application/parquet',
    '.feather': 'application/feather',
    '.orc': 'application/orc',

    # По умолчанию
    '': 'application/octet-stream',
}

# MIME-типы для категорий файлов
OCSET_STREAM_MIME_TYPES = {ext: mime for ext, mime in G_ALL_MIME_TYPES.items() if ext in G_OCSET_STREAM_FILE_TYPES}
TABLE_MIME_TYPES = {ext: mime for ext, mime in G_ALL_MIME_TYPES.items() if ext in G_TABLE_FILE_TYPES}
ARCH_MIME_TYPES = {ext: mime for ext, mime in G_ALL_MIME_TYPES.items() if ext in G_ARCH_FILE_TYPES}
DOCS_MIME_TYPES = {ext: mime for ext, mime in G_ALL_MIME_TYPES.items() if ext in G_DOCS_FILE_TYPES}
IMAGE_MIME_TYPES = {ext: mime for ext, mime in G_ALL_MIME_TYPES.items() if ext in G_IMAGE_FILE_TYPES}
VIDEO_MIME_TYPES = {ext: mime for ext, mime in G_ALL_MIME_TYPES.items() if ext in G_VIDEO_FILE_TYPES}


class S3Data:
    """Конфигурационные данные для работы с S3."""

    # Ключи доступа и параметры подключения
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.timeweb.cloud"

    # Версия подписи S3
    S3_SIGNATURE_VERS = 's3v4'

    # TLS(SSL)
    S3_USE_SSL = True
    S3_VERIFY = True

    # Время действия временных ссылок (в секундах)
    DEFAULT_LINK_EXPIRATION = 300

    # Настройки кэширования
    S3_CACHE_CONTROL = 'max-age=86400'
    S3_CACHE_CONTROL_ZERO = 'max-age=0'

    # ACL
    S3_ACL_PRIVATE = 'private'
    S3_ACL_PUBLIC_READ = "public-read"

    # Запись файлов с одинаковыми именами 
    S3_FILE_OVERWRITE_FALSE = False
    S3_FILE_OVERWRITE_TRUE = True

    # Аутентификация параметров запроса
    # из сгенерированных URL-адресов
    S3_QUERYSTRING_AUTH_TRUE = True
    S3_QUERYSTRING_AUTH_FALSE = False

    # Пути и обработчики
    STATIC_LOCATION = 'static'
    STATIC_BACKEND = 'app_config.s3_conf.CustomS3Storage'
    MEDIA_BACKEND = 'app_config.s3_conf.CustomS3Storage'
    MEDIA_LOCATION = 'media'

    # Разрешенные расширения файлов
    ALLOWED_FILE_EXTENSIONS = list(G_ALL_FILE_TYPES)
    ALLOWED_ARCH_EXTENSIONS = list(G_ARCH_FILE_TYPES)
    ALLOWED_DOCS_EXTENSIONS = list(G_DOCS_FILE_TYPES)
    ALLOWED_IMAGE_EXTENSIONS = list(G_IMAGE_FILE_TYPES)
    ALLOWED_VIDEO_EXTENSIONS = list(G_VIDEO_FILE_TYPES)

    # Ссылки на глобальные MIME-типы
    ALL_MIME_TYPES = G_ALL_MIME_TYPES
    ARCH_MIME_TYPES = ARCH_MIME_TYPES
    DOCS_MIME_TYPES = DOCS_MIME_TYPES
    IMAGE_MIME_TYPES = IMAGE_MIME_TYPES
    VIDEO_MIME_TYPES = VIDEO_MIME_TYPES

    # Типы файлов
    ARCH_FILE_TYPES = G_ARCH_FILE_TYPES
    DOCS_FILE_TYPES = G_DOCS_FILE_TYPES
    VIDEO_FILE_TYPES = G_VIDEO_FILE_TYPES
    IMAGE_FILE_TYPES = G_IMAGE_FILE_TYPES
    ALL_FILE_TYPES = {
        G_ARCH_FILE_TYPES: 'arch',
        G_DOCS_FILE_TYPES: 'file',
        G_VIDEO_FILE_TYPES: 'video',
        G_IMAGE_FILE_TYPES: 'image',
    }

    # Конфигурация клиента S3
    AWS_S3_CLIENT_CONFIG = Config(
        signature_version='s3v4',
        s3={
            'payload_signing_enabled': True,
            'addressing_style': 'path',
        },
        request_checksum_calculation='when_required',
        response_checksum_validation='when_required',
    )

    # Конфигурация передачи файлов
    S3_TRANSFER_CONFIG = TransferConfig(
        multipart_threshold=32 * MB,
        multipart_chunksize=16 * MB,
        max_concurrency=10,
    )

    # Максимальный размер загружаемого файла
    MAX_UPLOAD_SIZE = 100 * MB

    @staticmethod
    def validate_file_size(f):
        """
        Проверяет, что размер файла не превышает MAX_UPLOAD_SIZE.
        Args:
            f: Объект файла (например, InMemoryUploadedFile или TemporaryUploadedFile).
        Returns:
            Объект файла, если проверка пройдена.
        Raises:
            ValidationError: Если размер файла превышает MAX_UPLOAD_SIZE или файл недействителен.
        """
        # Проверка наличия атрибута size
        if not hasattr(f, 'size'):
            logger.error("Недопустимый объект файла: отсутствует атрибут размера")
            raise ValidationError(("Недопустимый объект файла: отсутствует атрибут размера"))

        # Проверка размера файла
        if f.size > S3Data.MAX_UPLOAD_SIZE:
            size_mb = f.size / MB
            max_mb = S3Data.MAX_UPLOAD_SIZE / MB
            msg = (
                "Файл слишком большой ({:.2f} МБ). Максимум {:.0f} МБ."
            ).format(size_mb, max_mb)
            logger.error(f"Проверка размера файла не удалась: {msg}")
            raise ValidationError(msg)

        return f


# Конфигурация:
# Django + S3
STORAGES_CONF = {
    "default": {
        "BACKEND": S3Data.MEDIA_BACKEND,
        "OPTIONS": {
            "access_key": S3Data.AWS_ACCESS_KEY_ID,
            "secret_key": S3Data.AWS_SECRET_ACCESS_KEY,
            "bucket_name": S3Data.AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": S3Data.AWS_S3_ENDPOINT_URL,
            "region_name": S3Data.AWS_S3_REGION_NAME,
            "signature_version": S3Data.S3_SIGNATURE_VERS,
            "location": S3Data.MEDIA_LOCATION,
            "use_ssl": S3Data.S3_USE_SSL,
            "verify": S3Data.S3_VERIFY,
            "default_acl": S3Data.S3_ACL_PRIVATE,
            "file_overwrite": S3Data.S3_FILE_OVERWRITE_FALSE,
            "querystring_auth": S3Data.S3_QUERYSTRING_AUTH_TRUE,
            "querystring_expire": S3Data.DEFAULT_LINK_EXPIRATION,
            "transfer_config": S3Data.S3_TRANSFER_CONFIG,
            "object_parameters": {
                "ACL": S3Data.S3_ACL_PRIVATE,
                "CacheControl": S3Data.S3_CACHE_CONTROL,
            },
            "client_config": S3Data.AWS_S3_CLIENT_CONFIG,
        },
    },
    "staticfiles": {
        "BACKEND": S3Data.STATIC_BACKEND,
        "OPTIONS": {
            "access_key": S3Data.AWS_ACCESS_KEY_ID,
            "secret_key": S3Data.AWS_SECRET_ACCESS_KEY,
            "bucket_name": S3Data.AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": S3Data.AWS_S3_ENDPOINT_URL,
            "region_name": S3Data.AWS_S3_REGION_NAME,
            "signature_version": S3Data.S3_SIGNATURE_VERS,
            "location": S3Data.STATIC_LOCATION,
            "use_ssl": S3Data.S3_USE_SSL,
            "verify": S3Data.S3_VERIFY,
            "default_acl": S3Data.S3_ACL_PUBLIC_READ,
            "querystring_auth": S3Data.S3_QUERYSTRING_AUTH_FALSE,
            "file_overwrite": S3Data.S3_FILE_OVERWRITE_TRUE,
            "transfer_config": S3Data.S3_TRANSFER_CONFIG,
            "object_parameters": {
                "ACL": S3Data.S3_ACL_PUBLIC_READ,
                "CacheControl": S3Data.S3_CACHE_CONTROL_ZERO,
            },
            "client_config": S3Data.AWS_S3_CLIENT_CONFIG,
        },
    },
}


# Кастомный обработчик
# для работы с хранилищем S3
class CustomS3Storage(S3Storage):
    """Кастомное хранилище S3 с улучшенной обработкой MIME-типов."""

    # Дефолтные значения
    default_access_key = S3Data.AWS_ACCESS_KEY_ID
    default_secret_key = S3Data.AWS_SECRET_ACCESS_KEY
    default_bucket_name = S3Data.AWS_STORAGE_BUCKET_NAME
    default_endpoint_url = S3Data.AWS_S3_ENDPOINT_URL
    default_region_name = S3Data.AWS_S3_REGION_NAME
    default_signature_version = S3Data.S3_SIGNATURE_VERS
    default_transfer_config = S3Data.S3_TRANSFER_CONFIG
    default_client_config = S3Data.AWS_S3_CLIENT_CONFIG
    default_use_ssl = S3Data.S3_USE_SSL
    default_verify = S3Data.S3_VERIFY
    default_default_acl = S3Data.S3_ACL_PRIVATE
    default_querystring_auth = S3Data.S3_QUERYSTRING_AUTH_TRUE
    default_file_overwrite = S3Data.S3_FILE_OVERWRITE_FALSE
    default_querystring_expire = S3Data.DEFAULT_LINK_EXPIRATION
    default_cache_control = S3Data.S3_CACHE_CONTROL

    def __init__(self, *args, **kwargs):
        # Устанавливаем дефолтные значения
        kwargs.setdefault("access_key", self.default_access_key)
        kwargs.setdefault("secret_key", self.default_secret_key)
        kwargs.setdefault("bucket_name", self.default_bucket_name)
        kwargs.setdefault("endpoint_url", self.default_endpoint_url)
        kwargs.setdefault("region_name", self.default_region_name)
        kwargs.setdefault("signature_version", self.default_signature_version)
        kwargs.setdefault("default_acl", self.default_default_acl)
        kwargs.setdefault("querystring_auth", self.default_querystring_auth)
        kwargs.setdefault("file_overwrite", self.default_file_overwrite)
        kwargs.setdefault("transfer_config", self.default_transfer_config)
        kwargs.setdefault("client_config", self.default_client_config)
        kwargs.setdefault("use_ssl", self.default_use_ssl)
        kwargs.setdefault("verify", self.default_verify)
        kwargs.setdefault("querystring_expire", self.default_querystring_expire)

        # object_parameters
        object_parameters = kwargs.get("object_parameters", {})
        object_parameters.setdefault("CacheControl", self.default_cache_control)
        object_parameters.setdefault("ACL", kwargs["default_acl"])
        kwargs["object_parameters"] = object_parameters

        super().__init__(*args, **kwargs)

        # Проверка обязательных параметров
        required_params = ["access_key", "secret_key", "bucket_name", "endpoint_url", "region_name"]
        for param in required_params:
            if not getattr(self, param, None):
                logger.error(f"Параметр {param} не установлен в CustomS3Storage.")
                raise ValueError(f"Параметр {param} обязателен для конфигурации S3.")
    
    def custom_guess_type(self, name):
        """Метод возвращает MIME ТИП"""
        # Приводим к нижнему регистру и убираем лишние пробелы
        name = name.lower().strip()

        # Проверяем известные сдвоенные расширения (например .tar.gz)
        double_exts = ['.tar.gz', '.tar.bz2', '.tar.xz', '.tar.Z']
        for ext in double_exts:
            if name.endswith(ext):
                content_type = S3Data.ALL_MIME_TYPES[ext]
                encoding = 'gzip' if ext.endswith('.gz') else 'bzip2' if ext.endswith('.bz2') else 'xz'
                return content_type, encoding

        # Ищем обычное расширение
        for ext in S3Data.ALL_MIME_TYPES:
            if ext and name.endswith(ext):
                content_type = S3Data.ALL_MIME_TYPES[ext]
                # Определяем encoding, если это архив
                if ext in ('.gz', '.Z'):
                    return content_type, 'gzip'
                elif ext in ('.bz2'):
                    return content_type, 'bzip2'
                elif ext in ('.xz'):
                    return content_type, 'xz'
                else:
                    return content_type, None

        # Если расширение не найдено
        logger.warning(f"MIME-тип для {name} не определен, используется application/octet-stream")
        return 'application/octet-stream', None


    def _save(self, name, content):
        """Переопределение метода сохранения файла с установкой корректных MIME-типов."""
        
        # Проверка расширения файла
        file_ext = Path(name).suffix.lower()
        if file_ext not in S3Data.ALLOWED_FILE_EXTENSIONS:
            logger.error(f"Файл {name} имеет недопустимое расширение {file_ext}.")
            raise ValueError(f"Расширение {file_ext} не разрешено для загрузки.")

        # Получение чистого имени файла
        cleaned_name = clean_name(name)
        name = self._normalize_name(cleaned_name)

        # Определение MIME-типа на основе имени файла
        content_type, encoding = self.custom_guess_type(name) #mimetypes.guess_type(name)
        if not content_type:
            logger.warning(f"MIME-тип для файла {name} не определен, используется application/octet-stream")
            content_type = "application/octet-stream"

        # Добавление charset для текстовых файлов
        if content_type.startswith("text/"):
            content_type += "; charset=utf-8"

        # Формирование параметров объекта
        params = self._get_write_parameters(name, content)
        params.update({
            "ContentType": content_type,
        })

        # Добавление кодировки, если она определена
        if encoding:
            params["ContentEncoding"] = encoding

        # Обновление параметров объекта
        self.object_parameters.update(params)

        # Подготовка контента
        if is_seekable(content):
            content.seek(0, os.SEEK_SET)

        content = ReadBytesWrapper(content)

        # Применение gzip-сжатия, если необходимо
        if (
            self.gzip
            and content_type in self.gzip_content_types
            and "ContentEncoding" not in params
        ):
            content = self._compress_content(content)
            params["ContentEncoding"] = "gzip"

        # Создание объекта S3 и загрузка файла
        original_close = content.close
        content.close = lambda: None
        try:
            obj = self.bucket.Object(name)
            obj.upload_fileobj(content, ExtraArgs=params, Config=self.transfer_config)
        except (ClientError, EndpointConnectionError, NoCredentialsError) as e:
            logger.error(f"Ошибка при загрузке файла {name} в S3: {str(e)}")
            raise
        finally:
            content.close = original_close

        return cleaned_name


# Конфигурации
class StoragesConf:
    @staticmethod
    def get_storage_conf_1():
        """Конфигурация для файлов с приватным доступом."""
        required_params = {
            "AWS_ACCESS_KEY_ID": S3Data.AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": S3Data.AWS_SECRET_ACCESS_KEY,
            "AWS_STORAGE_BUCKET_NAME": S3Data.AWS_STORAGE_BUCKET_NAME,
            "AWS_S3_ENDPOINT_URL": S3Data.AWS_S3_ENDPOINT_URL,
            "AWS_S3_REGION_NAME": S3Data.AWS_S3_REGION_NAME,
        }
        for param_name, param_value in required_params.items():
            if not param_value:
                logger.error(f"Параметр {param_name} не установлен.")
                raise ValueError(f"Параметр {param_name} обязателен для конфигурации S3.")

        return CustomS3Storage(
            access_key=S3Data.AWS_ACCESS_KEY_ID,
            secret_key=S3Data.AWS_SECRET_ACCESS_KEY,
            bucket_name=S3Data.AWS_STORAGE_BUCKET_NAME,
            endpoint_url=S3Data.AWS_S3_ENDPOINT_URL,
            region_name=S3Data.AWS_S3_REGION_NAME,
            signature_version=S3Data.S3_SIGNATURE_VERS,
            use_ssl=S3Data.S3_USE_SSL,
            verify=S3Data.S3_VERIFY,
            default_acl=S3Data.S3_ACL_PRIVATE,
            querystring_auth=S3Data.S3_QUERYSTRING_AUTH_TRUE,
            querystring_expire=S3Data.DEFAULT_LINK_EXPIRATION,
            file_overwrite=S3Data.S3_FILE_OVERWRITE_FALSE,
            transfer_config=S3Data.S3_TRANSFER_CONFIG,
            object_parameters={
                "ACL": S3Data.S3_ACL_PRIVATE,
                "CacheControl": S3Data.S3_CACHE_CONTROL_ZERO,
            },
            client_config=S3Data.AWS_S3_CLIENT_CONFIG,
        )

    @staticmethod
    def get_storage_conf_2():
        """Конфигурация для файлов с публичным доступом."""
        required_params = {
            "AWS_ACCESS_KEY_ID": S3Data.AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": S3Data.AWS_SECRET_ACCESS_KEY,
            "AWS_STORAGE_BUCKET_NAME": S3Data.AWS_STORAGE_BUCKET_NAME,
            "AWS_S3_ENDPOINT_URL": S3Data.AWS_S3_ENDPOINT_URL,
            "AWS_S3_REGION_NAME": S3Data.AWS_S3_REGION_NAME,
        }
        for param_name, param_value in required_params.items():
            if not param_value:
                logger.error(f"Параметр {param_name} не установлен.")
                raise ValueError(f"Параметр {param_name} обязателен для конфигурации S3.")

        return CustomS3Storage(
            access_key=S3Data.AWS_ACCESS_KEY_ID,
            secret_key=S3Data.AWS_SECRET_ACCESS_KEY,
            bucket_name=S3Data.AWS_STORAGE_BUCKET_NAME,
            endpoint_url=S3Data.AWS_S3_ENDPOINT_URL,
            region_name=S3Data.AWS_S3_REGION_NAME,
            signature_version=S3Data.S3_SIGNATURE_VERS,
            use_ssl=S3Data.S3_USE_SSL,
            verify=S3Data.S3_VERIFY,
            default_acl=S3Data.S3_ACL_PUBLIC_READ,
            querystring_auth=S3Data.S3_QUERYSTRING_AUTH_FALSE,
            file_overwrite=S3Data.S3_FILE_OVERWRITE_FALSE,
            transfer_config=S3Data.S3_TRANSFER_CONFIG,
            object_parameters={
                "ACL": S3Data.S3_ACL_PUBLIC_READ,
                "CacheControl": S3Data.S3_CACHE_CONTROL,
            },
            client_config=S3Data.AWS_S3_CLIENT_CONFIG,
        )