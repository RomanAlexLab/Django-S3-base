# app_storage/signals.py
#
# Этот файл содержит сигналы Django, связанные с удалением файлов из S3-хранилища.
# После удаления объекта модели из базы данных (post_delete), автоматически удаляется 
# соответствующий файл из облачного хранилища (S3).
#
# Для каждого типа медиафайла определён отдельный обработчик сигнала:
# - Публичные файлы: PublicImage, PublicVideo, PublicFile
# - Приватные файлы: PrivateImage, PrivateVideo, PrivateFile
# - Пользовательские файлы: MediaFile
#
# Файлы удаляются через соответствующее хранилище, заданное в StoragesConf:
# - StoragesConf.get_storage_conf_1() — для приватных файлов
# - StoragesConf.get_storage_conf_2() — для публичных файлов


import logging
from django.db.models.signals import post_delete
from django.dispatch import receiver
from app_config.s3_conf import StoragesConf
from .models import (
    PublicImage, PublicVideo, PublicFile,
    PrivateImage, PrivateVideo, PrivateFile, MediaFile
)


logger = logging.getLogger(__name__)


# ========================
# Сигналы публичных файлов
# ========================


@receiver(post_delete, sender=PublicImage)
def delete_public_image(sender, instance, **kwargs):
    """
    Удаляет публичное изображение из S3 после удаления модели.
    """
    storage = StoragesConf.get_storage_conf_2()
    key = getattr(instance, 'image', None) and instance.image.name
    if not key:
        return

    try:
        if storage.exists(key):
            storage.delete(key)
            logger.info(f"Удалено публичное изображение из S3: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении публичного изображения ({key}) из S3: {e}")


@receiver(post_delete, sender=PublicVideo)
def delete_public_video(sender, instance, **kwargs):
    """
    Удаляет публичное видео из S3 после удаления модели.
    """
    storage = StoragesConf.get_storage_conf_2()
    key = getattr(instance, 'video', None) and instance.video.name
    if not key:
        return

    try:
        if storage.exists(key):
            storage.delete(key)
            logger.info(f"Удалено публичное видео из S3: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении публичного видео ({key}) из S3: {e}")


@receiver(post_delete, sender=PublicFile)
def delete_public_file(sender, instance, **kwargs):
    """
    Удаляет публичный файл из S3 после удаления модели.
    """
    storage = StoragesConf.get_storage_conf_2()
    key = getattr(instance, 'file', None) and instance.file.name
    if not key:
        return

    try:
        if storage.exists(key):
            storage.delete(key)
            logger.info(f"Удалён публичный файл из S3: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении публичного файла ({key}) из S3: {e}")


# ========================
# Сигналы приватных файлов
# ========================


@receiver(post_delete, sender=PrivateImage)
def delete_private_image(sender, instance, **kwargs):
    """
    Удаляет приватное изображение из S3 после удаления модели.
    """
    storage = StoragesConf.get_storage_conf_1()
    key = getattr(instance, 'image', None) and instance.image.name
    if not key:
        return

    try:
        if storage.exists(key):
            storage.delete(key)
            logger.info(f"Удалено приватное изображение из S3: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении приватного изображения ({key}) из S3: {e}")


@receiver(post_delete, sender=PrivateVideo)
def delete_private_video(sender, instance, **kwargs):
    """
    Удаляет приватное видео из S3 после удаления модели.
    """
    storage = StoragesConf.get_storage_conf_1()
    key = getattr(instance, 'video', None) and instance.video.name
    if not key:
        return

    try:
        if storage.exists(key):
            storage.delete(key)
            logger.info(f"Удалено приватное видео из S3: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении приватного видео ({key}) из S3: {e}")


@receiver(post_delete, sender=PrivateFile)
def delete_private_file(sender, instance, **kwargs):
    """
    Удаляет приватный файл из S3 после удаления модели.
    """
    storage = StoragesConf.get_storage_conf_1()
    key = getattr(instance, 'file', None) and instance.file.name
    if not key:
        return

    try:
        if storage.exists(key):
            storage.delete(key)
            logger.info(f"Удалён приватный файл из S3: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении приватного файла ({key}) из S3: {e}")


@receiver(post_delete, sender=MediaFile)
def delete_media_file(sender, instance, **kwargs):
    """
    Удаляет пользовательский файл из S3 после удаления модели.
    """
    storage = StoragesConf.get_storage_conf_1()
    key = getattr(instance, 'file', None) and instance.file.name
    if not key:
        return

    try:
        if storage.exists(key):
            storage.delete(key)
            logger.info(f"Удалён пользовательский файл из S3: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении пользовательского файла ({key}) из S3: {e}")
