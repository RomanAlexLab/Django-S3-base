# app_storage/models.py
#
# Этот файл содержит модели публичных и приватных файлов.
# Каждая модель имеет метод `delete`, который удаляет файл из S3 
# перед удалением объекта из базы данных.
#
# Каждая модель также имеет переопределённый метод `save`, 
# который обеспечивает корректное сохранение файла в хранилище (например, в S3),
# используя указанный storage.
#
# Storage может быть задан либо на уровне поля 
# (например, models.FileField или models.ImageField), 
# либо явно вызван внутри метода при необходимости.

import logging
from django.db import models
from django.core.exceptions import ValidationError
from app_config.s3_conf import StoragesConf


logger = logging.getLogger(__name__)


# =======================
# Модели публичных файлов
# =======================


def public_image_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f'public/image/{instance.name}.{ext}'

def public_video_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f'public/video/{instance.name}.{ext}'

def public_file_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f'public/file/{instance.name}.{ext}'


class PublicImage(models.Model):
    name = models.CharField("Название", max_length=255)
    image = models.ImageField(
        "Публичное изображение",
        upload_to=public_image_upload_to,
        storage=StoragesConf.get_storage_conf_2,
    )

    class Meta:
        verbose_name = "Публичное изображение"
        verbose_name_plural = "Публичные изображения"

    def delete(self, *args, **kwargs):
        storage = StoragesConf.get_storage_conf_2()
        key = self.image.name
        try:
            if self.image and storage.exists(key):
                storage.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении PublicImage: ({key}): {e}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении PublicImage: {e}")
            raise ValidationError("Не удалось сохранить файл. Повторите попытку позже.")

    def __str__(self):
        return self.name


class PublicVideo(models.Model):
    name = models.CharField("Название", max_length=255)
    video = models.FileField(
        "Публичное видео",
        upload_to=public_video_upload_to,
        storage=StoragesConf.get_storage_conf_2,
    )

    class Meta:
        verbose_name = "Публичное видео"
        verbose_name_plural = "Публичные видео"

    def delete(self, *args, **kwargs):
        storage = StoragesConf.get_storage_conf_2()
        key = self.video.name
        try:
            if self.video and storage.exists(key):
                storage.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении PublicVideo: ({key}): {e}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении PublicVideo: {e}")
            raise ValidationError("Не удалось сохранить файл. Повторите попытку позже.")

    def __str__(self):
        return self.name


class PublicFile(models.Model):
    name = models.CharField("Название", max_length=255)
    file = models.FileField(
        "Публичный файл",
        upload_to=public_file_upload_to,
        storage=StoragesConf.get_storage_conf_2,
    )

    class Meta:
        verbose_name = "Публичный файл"
        verbose_name_plural = "Публичные файлы"

    def delete(self, *args, **kwargs):
        storage = StoragesConf.get_storage_conf_2()
        key = self.file.name
        try:
            if self.file and storage.exists(key):
                storage.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении PublicFile: ({key}): {e}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении PublicFile: {e}")
            raise ValidationError("Не удалось сохранить файл. Повторите попытку позже.")

    def __str__(self):
        return self.name


# =======================
# Модели приватных файлов
# =======================


def private_image_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f"private/image/{instance.name}.{ext}"

def private_video_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f"private/video/{instance.name}.{ext}"

def private_file_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f"private/file/{instance.name}.{ext}"

def media_file_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f"media/{instance.name}.{ext}"


class PrivateImage(models.Model):
    name = models.CharField("Название", max_length=255)
    image = models.ImageField(
        "Приватное изображение",
        upload_to=private_image_upload_to,
        storage=StoragesConf.get_storage_conf_1,
    )

    class Meta:
        verbose_name = "Приватное изображение"
        verbose_name_plural = "Приватные изображения"

    def delete(self, *args, **kwargs):
        storage = StoragesConf.get_storage_conf_1()
        key = self.image.name
        try:
            if self.image and storage.exists(key):
                storage.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении PrivateImage: ({key}): {e}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении PrivateImage: {e}")
            raise ValidationError("Не удалось сохранить файл. Повторите попытку позже.")

    def __str__(self):
        return self.name


class PrivateVideo(models.Model):
    name = models.CharField("Название", max_length=255)
    video = models.FileField(
        "Приватное видео",
        upload_to=private_video_upload_to,
        storage=StoragesConf.get_storage_conf_1,
    )

    class Meta:
        verbose_name = "Приватное видео"
        verbose_name_plural = "Приватные видео"

    def delete(self, *args, **kwargs):
        storage = StoragesConf.get_storage_conf_1()
        key = self.video.name
        try:
            if self.video and storage.exists(key):
                storage.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении PrivateVideo: ({key}): {e}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении PrivateVideo: {e}")
            raise ValidationError("Не удалось сохранить файл. Повторите попытку позже.")

    def __str__(self):
        return self.name


class PrivateFile(models.Model):
    name = models.CharField("Название", max_length=255)
    file = models.FileField(
        "Приватный файл",
        upload_to=private_file_upload_to,
        storage=StoragesConf.get_storage_conf_1,
    )

    class Meta:
        verbose_name = "Приватный файл"
        verbose_name_plural = "Приватные файлы"

    def delete(self, *args, **kwargs):
        storage = StoragesConf.get_storage_conf_1()
        key = self.file.name
        try:
            if self.file and storage.exists(key):
                storage.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении PrivateFile: ({key}): {e}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении PrivateFile: {e}")
            raise ValidationError("Не удалось сохранить файл. Повторите попытку позже.")

    def __str__(self):
        return self.name
    

class MediaFile(models.Model):
    name = models.CharField("Название", max_length=255)
    file = models.FileField(
        "Пользовательский файл",
        upload_to=media_file_upload_to,
        storage=StoragesConf.get_storage_conf_1,
    )

    class Meta:
        verbose_name = "Пользовательский файл"
        verbose_name_plural = "Пользовательские файлы"

    def delete(self, *args, **kwargs):
        storage = StoragesConf.get_storage_conf_1()
        key = self.file.name
        try:
            if self.file and storage.exists(key):
                storage.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении MediaFile: ({key}): {e}")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении MediaFile: {e}")
            raise ValidationError("Не удалось сохранить файл. Повторите попытку позже.")

    def __str__(self):
        return self.name
